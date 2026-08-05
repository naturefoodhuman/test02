# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 12:10:00

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
from dataclasses import asdict, dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, AsyncIterator

import httpx


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
    per_key_concurrency: int = 2
    queue_timeout_seconds: float = 900.0
    retry_after_cap_seconds: float = 900.0
    default_cooldown_seconds: float = 300.0
    max_attempts_per_request: int = 4
    connect_timeout_seconds: float = 30.0
    read_timeout_seconds: float = 300.0
    idle_ping_seconds: float = 10.0
    inbound_api_key: str | None = None

    @classmethod
    def from_env(cls) -> NIMProxySettings:
        return cls(
            upstream_base_url=os.getenv("NIM_PROXY_UPSTREAM_BASE_URL", cls.upstream_base_url).rstrip("/"),
            primary_model=os.getenv("NIM_PRIMARY_MODEL", cls.primary_model),
            fallback_model=os.getenv("NIM_FALLBACK_MODEL", cls.fallback_model),
            enable_fallback=_env_bool("NIM_PROXY_ENABLE_FALLBACK", False),
            per_key_rpm=int(os.getenv("NIM_PROXY_PER_KEY_RPM", str(cls.per_key_rpm))),
            per_key_concurrency=int(
                os.getenv("NIM_PROXY_PER_KEY_CONCURRENCY", str(cls.per_key_concurrency))
            ),
            queue_timeout_seconds=float(
                os.getenv("NIM_PROXY_QUEUE_TIMEOUT_SECONDS", str(cls.queue_timeout_seconds))
            ),
            retry_after_cap_seconds=float(
                os.getenv("NIM_PROXY_RETRY_AFTER_CAP_SECONDS", str(cls.retry_after_cap_seconds))
            ),
            default_cooldown_seconds=float(
                os.getenv("NIM_PROXY_DEFAULT_COOLDOWN_SECONDS", str(cls.default_cooldown_seconds))
            ),
            max_attempts_per_request=int(
                os.getenv("NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST", str(cls.max_attempts_per_request))
            ),
            connect_timeout_seconds=float(
                os.getenv("NIM_PROXY_CONNECT_TIMEOUT_SECONDS", str(cls.connect_timeout_seconds))
            ),
            read_timeout_seconds=float(
                os.getenv("NIM_PROXY_READ_TIMEOUT_SECONDS", str(cls.read_timeout_seconds))
            ),
            idle_ping_seconds=float(os.getenv("NIM_PROXY_IDLE_PING_SECONDS", str(cls.idle_ping_seconds))),
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
            "semaphore_locked": self.semaphore.locked(),
            "consecutive_429": self.consecutive_429,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }


class NoNIMKeyAvailable(RuntimeError):
    def __init__(self, wait_seconds: float) -> None:
        super().__init__(f"No NVIDIA NIM key available; retry after {wait_seconds:.1f}s")
        self.wait_seconds = wait_seconds


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

    def snapshot(self) -> dict[str, Any]:
        return {
            "key_count": len(self.keys),
            "keys": [key.snapshot() for key in self.keys],
            "affinity_size": len(self.affinity),
        }

    def session_key(self, session_id: str | None) -> NIMKeyState | None:
        if not session_id:
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
        candidates.sort(key=lambda key: (len(key.request_times), key.key_id))
        selected = candidates[0]
        if session_id:
            self.affinity[session_id] = selected.key_id
        return selected

    async def acquire(self, session_id: str | None = None) -> NIMKeyState:
        deadline = _now() + self.settings.queue_timeout_seconds
        while True:
            selected = self.pick_now(session_id)
            if selected is not None:
                await selected.semaphore.acquire()
                selected.reserve()
                return selected
            wait = min(key.available_in() for key in self.keys)
            if _now() + wait > deadline:
                raise NoNIMKeyAvailable(wait)
            await asyncio.sleep(min(max(wait, 0.05), 5.0))

    def release(self, key: NIMKeyState) -> None:
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
        attempted_fallback = False
        last_status = 503
        last_body = b""
        last_headers: dict[str, str] = {}
        for attempt in range(max(1, self.settings.max_attempts_per_request)):
            try:
                key = await self.pool.acquire(session_id=session_id)
            except NoNIMKeyAvailable as exc:
                return 429, {"retry-after": str(round(exc.wait_seconds, 3))}, json.dumps(
                    {"error": {"message": str(exc), "type": "rate_limit"}},
                    ensure_ascii=False,
                ).encode("utf-8")
            try:
                upstream_payload = build_upstream_payload(payload, decision)
                status, response_headers, body = await self._post_bytes(key, upstream_payload)
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
                if self.settings.enable_fallback and not attempted_fallback:
                    attempted_fallback = True
                    decision = ModelDecision(
                        requested_model=decision.requested_model,
                        upstream_model=self.settings.fallback_model,
                        used_fallback=True,
                    )
                    self.fallback_count += 1
                await asyncio.sleep(min(_jitter_backoff(attempt), 5.0))
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
        session_id = session_id_from_request(payload, headers)
        decision = normalize_model_name_for_nim(str(payload.get("model", "")), self.settings)
        try:
            key = await self.pool.acquire(session_id=session_id)
        except NoNIMKeyAvailable as exc:
            yield f"event: error\ndata: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n".encode()
            return
        try:
            upstream_payload = build_upstream_payload(payload, decision)
            async with self.http_client.stream(
                "POST",
                f"{self.settings.upstream_base_url}/chat/completions",
                json=upstream_payload,
                headers={"Authorization": f"Bearer {key.api_key}", "Content-Type": "application/json"},
            ) as response:
                if response.status_code == 429:
                    key.mark_429(response.headers.get("Retry-After"))
                elif response.status_code == 200:
                    key.mark_success()
                else:
                    key.mark_retryable_error()
                if response.status_code != 200:
                    body = await response.aread()
                    yield f"event: error\ndata: {body.decode('utf-8', errors='ignore')}\n\n".encode()
                    return
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
        finally:
            self.pool.release(key)


def _jitter_backoff(attempt: int) -> float:
    return min(2 ** attempt, 30.0) + random.uniform(0.0, 0.25)


def create_app():
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.responses import Response, StreamingResponse

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
