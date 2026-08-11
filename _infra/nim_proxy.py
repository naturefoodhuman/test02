# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-11 18:20:00

"""NVIDIA NIM OpenAI-compatible sidecar proxy.

Purpose:
- keep Claude Code / smart_proxy from hitting NVIDIA NIM directly;
- use indexed personal keys (NVIDIA_API_KEY_1, NVIDIA_API_KEY_2, ...);
- enforce per-key RPM/concurrency limits;
- honor Retry-After and put keys into cooldown instead of hammering 429;
- optionally fall back from GLM-5.2 to a same-tier model when enabled.

This sidecar is intentionally self-contained and can be run locally:

    python3 _infra/nim_proxy.py

It exposes /v1/chat/completions and /stats.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import time
from collections import deque
from dataclasses import asdict, dataclass, field, fields
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, AsyncIterator

import httpx



def load_dotenv_if_present(env_path: Path | str = ".env") -> int:
    """Load simple KEY=VALUE lines without overriding existing environment variables."""

    path = Path(env_path)
    if not path.exists():
        return 0
    loaded = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _now() -> float:
    return time.monotonic()


@dataclass(frozen=True, slots=True)
class NIMProxySettings:
    upstream_base_url: str = "https://integrate.api.nvidia.com/v1"
    primary_model: str = "z-ai/glm-5.2"
    fallback_model: str = "deepseek-ai/DeepSeek-V4-Pro"
    enable_fallback: bool = False
    per_key_rpm: int = 35
    per_key_concurrency: int = 1
    queue_timeout_seconds: float = 900.0
    retry_after_cap_seconds: float = 900.0
    default_cooldown_seconds: float = 300.0
    max_attempts_per_request: int = 1
    connect_timeout_seconds: float = 30.0
    read_timeout_seconds: float = 120.0
    request_wall_timeout_seconds: float = 180.0
    idle_ping_seconds: float = 10.0
    session_affinity: bool = False
    inbound_api_key: str | None = None

    @classmethod
    def from_env(cls) -> NIMProxySettings:
        defaults = {item.name: item.default for item in fields(cls)}
        return cls(
            upstream_base_url=os.getenv(
                "NIM_PROXY_UPSTREAM_BASE_URL",
                str(defaults["upstream_base_url"]),
            ).rstrip("/"),
            primary_model=os.getenv("NIM_PRIMARY_MODEL", str(defaults["primary_model"])),
            fallback_model=os.getenv("NIM_FALLBACK_MODEL", str(defaults["fallback_model"])),
            enable_fallback=_env_bool("NIM_PROXY_ENABLE_FALLBACK", False),
            per_key_rpm=int(os.getenv("NIM_PROXY_PER_KEY_RPM", str(defaults["per_key_rpm"]))),
            per_key_concurrency=int(
                os.getenv("NIM_PROXY_PER_KEY_CONCURRENCY", str(defaults["per_key_concurrency"]))
            ),
            queue_timeout_seconds=float(
                os.getenv("NIM_PROXY_QUEUE_TIMEOUT_SECONDS", str(defaults["queue_timeout_seconds"]))
            ),
            retry_after_cap_seconds=float(
                os.getenv("NIM_PROXY_RETRY_AFTER_CAP_SECONDS", str(defaults["retry_after_cap_seconds"]))
            ),
            default_cooldown_seconds=float(
                os.getenv("NIM_PROXY_DEFAULT_COOLDOWN_SECONDS", str(defaults["default_cooldown_seconds"]))
            ),
            max_attempts_per_request=int(
                os.getenv("NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST", str(defaults["max_attempts_per_request"]))
            ),
            connect_timeout_seconds=float(
                os.getenv("NIM_PROXY_CONNECT_TIMEOUT_SECONDS", str(defaults["connect_timeout_seconds"]))
            ),
            read_timeout_seconds=float(
                os.getenv("NIM_PROXY_READ_TIMEOUT_SECONDS", str(defaults["read_timeout_seconds"]))
            ),
            request_wall_timeout_seconds=float(
                os.getenv(
                    "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS",
                    str(defaults["request_wall_timeout_seconds"]),
                )
            ),
            idle_ping_seconds=float(
                os.getenv("NIM_PROXY_IDLE_PING_SECONDS", str(defaults["idle_ping_seconds"]))
            ),
            session_affinity=_env_bool("NIM_PROXY_SESSION_AFFINITY", bool(defaults["session_affinity"])),
            inbound_api_key=os.getenv("NIM_PROXY_API_KEY") or None,
        )


def load_indexed_nvidia_keys(prefix: str = "NVIDIA_API_KEY_", max_keys: int = 10) -> list[str]:
    """Load NVIDIA_API_KEY_1..NVIDIA_API_KEY_N; no secrets are logged or returned with ids."""

    keys: list[str] = []
    for index in range(1, max_keys + 1):
        value = os.getenv(f"{prefix}{index}")
        if value and value.strip():
            keys.append(value.strip())
    return keys


def retry_after_to_seconds(value: str | None, *, default: float, cap: float) -> float:
    if value:
        try:
            return min(max(0.0, float(value)), cap)
        except (TypeError, ValueError):
            try:
                parsed = parsedate_to_datetime(value)
                return min(max(0.0, parsed.timestamp() - time.time()), cap)
            except Exception:
                pass
    return min(default, cap)


@dataclass(slots=True)
class NIMKeyState:
    key_id: str
    api_key: str
    rpm: int
    concurrency: int
    default_cooldown_seconds: float
    retry_after_cap_seconds: float
    request_times: deque[float] = field(default_factory=deque)
    cooldown_until: float = 0.0
    consecutive_429: int = 0
    success_count: int = 0
    error_count: int = 0
    in_flight: int = 0
    semaphore: asyncio.Semaphore = field(init=False)

    def __post_init__(self) -> None:
        self.semaphore = asyncio.Semaphore(self.concurrency)

    def scrub_old(self, now: float | None = None) -> None:
        current = _now() if now is None else now
        while self.request_times and current - self.request_times[0] >= 60.0:
            self.request_times.popleft()

    def available_in(self, now: float | None = None) -> float:
        current = _now() if now is None else now
        self.scrub_old(current)
        waits = [max(0.0, self.cooldown_until - current)]
        if len(self.request_times) >= self.rpm:
            waits.append(max(0.0, 60.0 - (current - self.request_times[0])))
        return max(waits)

    def can_send_now(self, now: float | None = None) -> bool:
        return self.available_in(now) <= 0.0 and not self.semaphore.locked()

    def reserve(self, now: float | None = None) -> None:
        current = _now() if now is None else now
        self.scrub_old(current)
        self.request_times.append(current)

    def mark_success(self) -> None:
        self.consecutive_429 = 0
        self.success_count += 1

    def mark_retryable_error(self) -> None:
        self.error_count += 1

    def mark_429(self, retry_after: str | None = None) -> float:
        self.consecutive_429 += 1
        self.error_count += 1
        wait = retry_after_to_seconds(
            retry_after,
            default=self.default_cooldown_seconds,
            cap=self.retry_after_cap_seconds,
        )
        self.cooldown_until = max(self.cooldown_until, _now() + wait)
        return wait

    def snapshot(self) -> dict[str, Any]:
        wait = self.available_in()
        return {
            "key_id": self.key_id,
            "available_in_seconds": round(wait, 3),
            "in_cooldown": wait > 0,
            "recent_rpm": len(self.request_times),
            "rpm_limit": self.rpm,
            "concurrency_limit": self.concurrency,
            "in_flight": self.in_flight,
            "semaphore_locked": self.semaphore.locked(),
            "consecutive_429": self.consecutive_429,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }


class NoNIMKeyAvailable(RuntimeError):
    def __init__(self, wait_seconds: float, reason: str = "rate_limit") -> None:
        super().__init__(f"No NVIDIA NIM key available; retry after {wait_seconds:.1f}s")
        self.wait_seconds = wait_seconds
        self.reason = reason


class NIMKeyPool:
    def __init__(self, keys: list[str], settings: NIMProxySettings) -> None:
        if not keys:
            raise ValueError("No NVIDIA NIM keys configured; set NVIDIA_API_KEY_1, NVIDIA_API_KEY_2, ...")
        self.settings = settings
        self.keys = [
            NIMKeyState(
                key_id=f"key-{index}",
                api_key=key,
                rpm=settings.per_key_rpm,
                concurrency=settings.per_key_concurrency,
                default_cooldown_seconds=settings.default_cooldown_seconds,
                retry_after_cap_seconds=settings.retry_after_cap_seconds,
            )
            for index, key in enumerate(keys, start=1)
        ]
        self.affinity: dict[str, str] = {}
        self._cursor = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "key_count": len(self.keys),
            "keys": [key.snapshot() for key in self.keys],
            "affinity_size": len(self.affinity),
        }

    def session_key(self, session_id: str | None) -> NIMKeyState | None:
        if not self.settings.session_affinity or not session_id:
            return None
        key_id = self.affinity.get(session_id)
        if not key_id:
            return None
        return next((item for item in self.keys if item.key_id == key_id), None)

    def pick_now(self, session_id: str | None = None) -> NIMKeyState | None:
        sticky = self.session_key(session_id)
        if sticky and sticky.can_send_now():
            return sticky
        candidates = [key for key in self.keys if key.can_send_now()]
        if not candidates:
            return None

        # Do not sort only by key_id: when requests are spaced more than 60s
        # apart, recent_rpm is often 0 for every key and key-1 wins forever.
        # Prefer lower in-flight load, then lower recent RPM, then lower lifetime
        # usage/error count so a cold key catches up quickly. A tiny round-robin
        # cursor breaks perfect ties without exposing raw key material.
        candidate_ids = {id(key) for key in candidates}
        ordered = sorted(
            ((index, key) for index, key in enumerate(self.keys) if id(key) in candidate_ids),
            key=lambda item: (
                item[1].in_flight,
                len(item[1].request_times),
                item[1].success_count + item[1].error_count,
                item[1].error_count,
                (item[0] - self._cursor) % len(self.keys),
            ),
        )
        selected_index, selected = ordered[0]
        self._cursor = (selected_index + 1) % len(self.keys)
        if self.settings.session_affinity and session_id:
            self.affinity[session_id] = selected.key_id
        return selected

    async def acquire(self, session_id: str | None = None) -> NIMKeyState:
        deadline = _now() + self.settings.queue_timeout_seconds
        while True:
            selected = self.pick_now(session_id)
            if selected is not None:
                await selected.semaphore.acquire()
                selected.in_flight += 1
                selected.reserve()
                return selected

            current = _now()
            waits = [key.available_in(current) for key in self.keys]
            # If a key is otherwise available but its semaphore is locked, the
            # bottleneck is local busy capacity, not NVIDIA Retry-After/RPM. Poll
            # briefly so a finishing request frees the key quickly. If this lasts
            # beyond queue_timeout_seconds, return a clear busy error instead of
            # misleading retry-after: 0.0.
            busy_capacity = any(
                wait <= 0.0 and key.semaphore.locked()
                for key, wait in zip(self.keys, waits)
            )
            if busy_capacity:
                wait = 1.0
                reason = "busy"
            else:
                wait = min(waits)
                reason = "rate_limit"
            if current + wait > deadline:
                raise NoNIMKeyAvailable(max(wait, 1.0), reason=reason)
            await asyncio.sleep(min(max(wait, 0.05), 5.0))

    def release(self, key: NIMKeyState) -> None:
        key.in_flight = max(0, key.in_flight - 1)
        key.semaphore.release()


@dataclass(frozen=True, slots=True)
class ModelDecision:
    requested_model: str
    upstream_model: str
    used_fallback: bool = False


def normalize_model_name_for_nim(requested_model: str | None, settings: NIMProxySettings) -> ModelDecision:
    raw = (requested_model or "").replace("openai/", "")
    if not raw or raw.startswith("claude-"):
        return ModelDecision(requested_model=raw, upstream_model=settings.primary_model)
    return ModelDecision(requested_model=raw, upstream_model=raw)


def session_id_from_request(payload: dict[str, Any], headers: dict[str, str] | None = None) -> str:
    header_value = ""
    if headers:
        header_value = headers.get("x-forge-session-id") or headers.get("x-session-id") or ""
    if header_value:
        return header_value
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    for key in ("session_id", "conversation_id", "thread_id"):
        if metadata.get(key):
            return str(metadata[key])
    if payload.get("user"):
        return str(payload["user"])
    messages = payload.get("messages") or []
    latest_user = ""
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                latest_user = json.dumps(message.get("content", ""), ensure_ascii=False, sort_keys=True)
                break
    digest_source = f"{payload.get('model', '')}:{latest_user[:2048]}"
    return hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]


def build_upstream_payload(
    payload: dict[str, Any],
    decision: ModelDecision,
) -> dict[str, Any]:
    upstream_payload = dict(payload)
    upstream_payload["model"] = decision.upstream_model
    upstream_payload.setdefault("stream", False)
    return upstream_payload


class NIMProxyService:
    def __init__(
        self,
        pool: NIMKeyPool,
        settings: NIMProxySettings,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.pool = pool
        self.settings = settings
        self.http_client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.connect_timeout_seconds,
                read=settings.read_timeout_seconds,
                write=30.0,
                pool=30.0,
            )
        )
        self.request_count = 0
        self.retry_count = 0
        self.fallback_count = 0

    def stats(self) -> dict[str, Any]:
        return {
            "request_count": self.request_count,
            "retry_count": self.retry_count,
            "fallback_count": self.fallback_count,
            "settings": {
                "upstream_base_url": self.settings.upstream_base_url,
                "primary_model": self.settings.primary_model,
                "fallback_model": self.settings.fallback_model,
                "enable_fallback": self.settings.enable_fallback,
                "per_key_rpm": self.settings.per_key_rpm,
                "per_key_concurrency": self.settings.per_key_concurrency,
                "max_attempts_per_request": self.settings.max_attempts_per_request,
                "read_timeout_seconds": self.settings.read_timeout_seconds,
                "request_wall_timeout_seconds": self.settings.request_wall_timeout_seconds,
                "session_affinity": self.settings.session_affinity,
            },
            "pool": self.pool.snapshot(),
        }

    async def forward_non_stream(
        self,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        self.request_count += 1
        session_id = session_id_from_request(payload, headers)
        decision = normalize_model_name_for_nim(str(payload.get("model", "")), self.settings)
        fallback_used = False
        last_status = 503
        last_body = b""
        last_headers: dict[str, str] = {}
        attempts_used_for_model = 0
        max_attempts = max(1, self.settings.max_attempts_per_request)

        while attempts_used_for_model < max_attempts:
            try:
                key = await self.pool.acquire(session_id=session_id)
            except NoNIMKeyAvailable as exc:
                status_code = 503 if exc.reason == "busy" else 429
                return status_code, {"retry-after": str(round(max(exc.wait_seconds, 1.0), 3))}, json.dumps(
                    {"error": {"message": str(exc), "type": exc.reason}},
                    ensure_ascii=False,
                ).encode("utf-8")
            try:
                upstream_payload = build_upstream_payload(payload, decision)
                try:
                    status, response_headers, body = await asyncio.wait_for(
                        self._post_bytes(key, upstream_payload),
                        timeout=self.settings.request_wall_timeout_seconds,
                    )
                except (
                    asyncio.TimeoutError,
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.RemoteProtocolError,
                ) as exc:
                    status = 504
                    response_headers = {}
                    body = json.dumps(
                        {
                            "error": {
                                "message": str(exc) or repr(exc),
                                "type": type(exc).__name__,
                                "model": decision.upstream_model,
                            }
                        },
                        ensure_ascii=False,
                    ).encode("utf-8")
                attempts_used_for_model += 1
                last_status, last_headers, last_body = status, response_headers, body
                if status == 200:
                    key.mark_success()
                    return status, response_headers, body
                self.retry_count += 1
                if status == 429:
                    key.mark_429(response_headers.get("retry-after") or response_headers.get("Retry-After"))
                elif status in {502, 503, 504}:
                    key.mark_retryable_error()
                else:
                    key.mark_retryable_error()
                    return status, response_headers, body
                if self.settings.enable_fallback and not fallback_used:
                    fallback_used = True
                    decision = ModelDecision(
                        requested_model=decision.requested_model,
                        upstream_model=self.settings.fallback_model,
                        used_fallback=True,
                    )
                    attempts_used_for_model = 0
                    self.fallback_count += 1
                    continue
                if attempts_used_for_model < max_attempts:
                    await asyncio.sleep(min(_jitter_backoff(attempts_used_for_model - 1), 5.0))
            finally:
                self.pool.release(key)
        return last_status, last_headers, last_body

    async def _post_bytes(
        self,
        key: NIMKeyState,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, str], bytes]:
        response = await self.http_client.post(
            f"{self.settings.upstream_base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key.api_key}", "Content-Type": "application/json"},
        )
        return response.status_code, dict(response.headers), response.content

    async def forward_stream(
        self,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[bytes]:
        self.request_count += 1
        session_id = session_id_from_request(payload, headers)
        decision = normalize_model_name_for_nim(str(payload.get("model", "")), self.settings)
        fallback_used = False
        last_error: dict[str, Any] | None = None

        while True:
            try:
                key = await self.pool.acquire(session_id=session_id)
            except NoNIMKeyAvailable as exc:
                payload_json = json.dumps(
                    {"error": {"message": str(exc), "type": exc.reason}},
                    ensure_ascii=False,
                )
                yield f"event: error\ndata: {payload_json}\n\n".encode()
                return

            should_try_fallback = False
            emitted_any = False
            try:
                upstream_payload = build_upstream_payload(payload, decision)
                try:
                    async with self.http_client.stream(
                        "POST",
                        f"{self.settings.upstream_base_url}/chat/completions",
                        json=upstream_payload,
                        headers={
                            "Authorization": f"Bearer {key.api_key}",
                            "Content-Type": "application/json",
                        },
                    ) as response:
                        if response.status_code == 200:
                            try:
                                deadline = _now() + self.settings.request_wall_timeout_seconds
                                byte_iter = response.aiter_bytes().__aiter__()
                                while True:
                                    remaining = deadline - _now()
                                    if remaining <= 0:
                                        raise asyncio.TimeoutError(
                                            f"stream exceeded {self.settings.request_wall_timeout_seconds:.0f}s wall timeout"
                                        )
                                    try:
                                        chunk = await asyncio.wait_for(byte_iter.__anext__(), timeout=remaining)
                                    except StopAsyncIteration:
                                        break
                                    if chunk:
                                        emitted_any = True
                                        yield chunk
                                key.mark_success()
                                return
                            except Exception as exc:
                                self.retry_count += 1
                                key.mark_retryable_error()
                                last_error = {
                                    "error": {
                                        "message": str(exc) or repr(exc),
                                        "type": type(exc).__name__,
                                        "model": decision.upstream_model,
                                    }
                                }
                                should_try_fallback = not emitted_any
                        else:
                            body = await response.aread()
                            body_text = body.decode("utf-8", errors="ignore")
                            self.retry_count += 1
                            if response.status_code == 429:
                                key.mark_429(response.headers.get("Retry-After"))
                            else:
                                key.mark_retryable_error()
                            last_error = {
                                "error": {
                                    "message": body_text,
                                    "type": f"HTTP{response.status_code}",
                                    "model": decision.upstream_model,
                                }
                            }
                            should_try_fallback = response.status_code in {429, 502, 503, 504}
                except (
                    asyncio.TimeoutError,
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.RemoteProtocolError,
                ) as exc:
                    self.retry_count += 1
                    key.mark_retryable_error()
                    last_error = {
                        "error": {
                            "message": str(exc) or repr(exc),
                            "type": type(exc).__name__,
                            "model": decision.upstream_model,
                        }
                    }
                    should_try_fallback = True
            finally:
                self.pool.release(key)

            if self.settings.enable_fallback and should_try_fallback and not fallback_used:
                fallback_used = True
                decision = ModelDecision(
                    requested_model=decision.requested_model,
                    upstream_model=self.settings.fallback_model,
                    used_fallback=True,
                )
                self.fallback_count += 1
                continue

            payload_json = json.dumps(last_error or {"error": {"message": "unknown stream error"}}, ensure_ascii=False)
            yield f"event: error\ndata: {payload_json}\n\n".encode()
            return


def _jitter_backoff(attempt: int) -> float:
    return min(2 ** attempt, 30.0) + random.uniform(0.0, 0.25)


def create_app():
    load_dotenv_if_present(Path(__file__).resolve().parents[1] / ".env")
    load_dotenv_if_present(Path.cwd() / ".env")

    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.responses import Response, StreamingResponse

    # With `from __future__ import annotations`, FastAPI resolves the `Request`
    # annotation through module globals at route-registration time. The import is
    # intentionally local to keep light unit tests from requiring FastAPI at module
    # import, so expose the class globally before declaring route handlers.
    globals()["Request"] = Request

    settings = NIMProxySettings.from_env()
    keys = load_indexed_nvidia_keys()
    service = NIMProxyService(NIMKeyPool(keys, settings), settings)
    app = FastAPI(title="FORGE NVIDIA NIM Proxy", version="0.1.0")

    def _check_inbound(auth: str | None) -> None:
        if settings.inbound_api_key is None:
            return
        expected = f"Bearer {settings.inbound_api_key}"
        if auth != expected:
            raise HTTPException(status_code=401, detail="invalid nim proxy bearer token")

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {"status": "ok", "key_count": len(service.pool.keys)}

    @app.get("/stats")
    async def stats() -> dict[str, Any]:
        return service.stats()

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request, authorization: str | None = Header(default=None)):
        _check_inbound(authorization)
        payload = await request.json()
        headers = {k.lower(): v for k, v in request.headers.items()}
        if bool(payload.get("stream", False)):
            return StreamingResponse(
                service.forward_stream(payload, headers),
                media_type="text/event-stream",
            )
        status, response_headers, body = await service.forward_non_stream(payload, headers)
        return Response(
            content=body,
            status_code=status,
            media_type=response_headers.get("content-type", "application/json"),
            headers={k: v for k, v in response_headers.items() if k.lower() == "retry-after"},
        )

    return app


def main() -> None:
    import uvicorn

    host = os.getenv("NIM_PROXY_HOST", "127.0.0.1")
    port = int(os.getenv("NIM_PROXY_PORT", "4010"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
