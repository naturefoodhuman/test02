# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-16 13:30:00

"""NVIDIA NIM sidecar proxy unit tests."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import httpx
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from _infra.nim_proxy import (  # noqa: E402
    NIMKeyPool,
    NIMProxyService,
    NIMProxySettings,
    build_upstream_payload,
    load_indexed_nvidia_keys,
    normalize_model_name_for_nim,
    retry_after_to_seconds,
    session_id_from_request,
)


class FakeClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.payloads: list[dict[str, object]] = []
        self.auth_headers: list[str] = []

    async def post(self, url: str, json=None, headers=None):  # type: ignore[no-untyped-def]
        self.payloads.append(json or {})
        self.auth_headers.append((headers or {}).get("Authorization", ""))
        return self.responses.pop(0)


def _settings(**overrides: object) -> NIMProxySettings:
    data = {
        "per_key_rpm": 2,
        "per_key_concurrency": 1,
        "queue_timeout_seconds": 0.05,
        "default_cooldown_seconds": 0.1,
        "retry_after_cap_seconds": 1.0,
        "max_attempts_per_request": 3,
    }
    data.update(overrides)
    return NIMProxySettings(**data)


def test_load_indexed_nvidia_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY_1", "k1")
    monkeypatch.setenv("NVIDIA_API_KEY_2", "k2")
    monkeypatch.delenv("NVIDIA_API_KEY_3", raising=False)

    assert load_indexed_nvidia_keys(max_keys=3) == ["k1", "k2"]


def test_retry_after_to_seconds_caps_values() -> None:
    assert retry_after_to_seconds("5", default=1, cap=3) == 3
    assert retry_after_to_seconds(None, default=2, cap=3) == 2
    assert retry_after_to_seconds("bad", default=4, cap=3) == 3


def test_model_alias_maps_claude_to_primary() -> None:
    decision = normalize_model_name_for_nim("claude-opus-4-8", _settings())

    assert decision.upstream_model == "z-ai/glm-5.2"
    assert build_upstream_payload({"model": "claude-opus-4-8"}, decision)["model"] == "z-ai/glm-5.2"


def test_session_id_is_stable_for_same_conversation() -> None:
    payload = {"model": "x", "messages": [{"role": "user", "content": "hello"}]}

    assert session_id_from_request(payload) == session_id_from_request(payload)
    assert session_id_from_request(payload, {"x-forge-session-id": "s1"}) == "s1"


def test_key_pool_session_affinity_and_cooldown() -> None:
    pool = NIMKeyPool(["k1", "k2"], _settings())
    first = pool.pick_now("session-a")
    assert first is not None
    first.mark_429("0.2")

    second = pool.pick_now("session-a")
    assert second is not None
    assert second.key_id != first.key_id


def test_key_pool_balances_repeated_requests_without_affinity() -> None:
    settings = _settings(session_affinity=False, per_key_rpm=100)
    pool = NIMKeyPool(["k1", "k2"], settings)

    first = pool.pick_now("same-session")
    assert first is not None
    first.mark_success()
    second = pool.pick_now("same-session")

    assert second is not None
    assert second.key_id != first.key_id


def test_key_pool_can_keep_session_affinity_when_enabled() -> None:
    settings = _settings(session_affinity=True, per_key_rpm=100)
    pool = NIMKeyPool(["k1", "k2"], settings)

    first = pool.pick_now("same-session")
    assert first is not None
    first.mark_success()
    second = pool.pick_now("same-session")

    assert second is not None
    assert second.key_id == first.key_id


def test_forward_non_stream_returns_busy_when_all_keys_are_locked() -> None:
    async def scenario() -> None:
        settings = _settings(per_key_concurrency=1, queue_timeout_seconds=0.01)
        pool = NIMKeyPool(["k1"], settings)
        locked = await pool.acquire()
        try:
            service = NIMProxyService(pool, settings, http_client=FakeClient([]))  # type: ignore[arg-type]
            status, headers, body = await service.forward_non_stream(
                {"model": "z-ai/glm-5.2", "messages": [], "stream": False}
            )
        finally:
            pool.release(locked)

        assert status == 503
        assert float(headers["retry-after"]) >= 1.0
        assert b"busy" in body

    asyncio.run(scenario())


def test_forward_non_stream_retries_after_429_with_next_key(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        async def no_sleep(_seconds: float) -> None:
            return None

        monkeypatch.setattr(asyncio, "sleep", no_sleep)
        fake = FakeClient(
            [
                httpx.Response(429, json={"error": "rate"}, headers={"Retry-After": "0.1"}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        pool = NIMKeyPool(["k1", "k2"], _settings())
        service = NIMProxyService(pool, _settings(), http_client=fake)  # type: ignore[arg-type]

        status, _headers, body = await service.forward_non_stream(
            {"model": "claude-opus-4-8", "messages": [], "stream": False}
        )

        assert status == 200
        assert b"ok" in body
        assert fake.auth_headers == ["Bearer k1", "Bearer k2"]
        assert service.retry_count == 1

    asyncio.run(scenario())


def test_forward_non_stream_can_use_configurable_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        async def no_sleep(_seconds: float) -> None:
            return None

        monkeypatch.setattr(asyncio, "sleep", no_sleep)
        fake = FakeClient(
            [
                httpx.Response(503, json={"error": "busy"}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        settings = _settings(enable_fallback=True)
        service = NIMProxyService(
            NIMKeyPool(["k1", "k2"], settings),
            settings,
            http_client=fake,  # type: ignore[arg-type]
        )

        status, _headers, body = await service.forward_non_stream(
            {"model": "z-ai/glm-5.2", "messages": [], "stream": False}
        )

        assert status == 200
        assert b"ok" in body
        assert fake.payloads[0]["model"] == "z-ai/glm-5.2"
        assert fake.payloads[1]["model"] == "deepseek-ai/DeepSeek-V4-Pro"
        assert service.fallback_count == 1

    asyncio.run(scenario())



def test_forge_start_integrates_nim_proxy_when_enabled() -> None:
    source = Path("scripts/forge-start.sh").read_text(encoding="utf-8")

    assert "load_forge_env" in source
    assert "start_nim_proxy_if_enabled" in source
    assert "FORGE_USE_NIM_PROXY" in source
    assert "NVIDIA_API_KEY_" in source
    assert "http://${NIM_PROXY_HOST}:${NIM_PROXY_PORT}/healthz" in source


def test_smart_proxy_has_nim_route_rewrite_switch() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "FORGE_USE_NIM_PROXY" in source
    assert "NIM_PROXY_BASE_URL" in source
    assert "api_key_optional" in source
    assert "integrate.api.nvidia.com" in source


def test_start_nim_proxy_loads_env_and_requires_indexed_keys() -> None:
    source = Path("scripts/start-nim-proxy.sh").read_text(encoding="utf-8")

    assert "load_env_file" in source
    assert 'source ".env"' not in source
    assert "tr -d" in source and "raw_line" in source
    assert "NVIDIA_API_KEY_${i}" in source
    assert "No NVIDIA NIM keys configured" in source


def test_smart_proxy_skips_global_rpm_guard_for_nim_sidecar_routes() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "api_key_optional" in source
    assert "skip rpm_guard for api_key_optional routes" in source
    assert 'if not remote_route.get("api_key_optional"):' in source



def test_forge_start_uses_bash3_safe_nim_enable_check() -> None:
    source = Path("scripts/forge-start.sh").read_text(encoding="utf-8")

    assert "${enabled,,}" not in source
    assert "enabled_lc" in source
    assert "tr '[:upper:]' '[:lower:]'" in source
    assert 'source "$env_file"' not in source
    assert "load_forge_env_file" in source
    assert "start_nim_proxy_if_enabled || exit 1" in source


def test_nim_proxy_settings_from_env_uses_real_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [
        "NIM_PROXY_UPSTREAM_BASE_URL",
        "NIM_PRIMARY_MODEL",
        "NIM_FALLBACK_MODEL",
        "NIM_PROXY_PER_KEY_RPM",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = NIMProxySettings.from_env()

    assert settings.upstream_base_url == "https://integrate.api.nvidia.com/v1"
    assert settings.primary_model == "z-ai/glm-5.2"
    assert settings.fallback_model == "deepseek-ai/DeepSeek-V4-Pro"
    assert settings.per_key_rpm == 35
    assert settings.per_key_concurrency == 1
    assert settings.request_wall_timeout_seconds == 180.0
    assert settings.session_affinity is False


def test_create_app_chat_route_treats_request_as_fastapi_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    try:
        from fastapi.testclient import TestClient
    except Exception:  # pragma: no cover - optional dependency in minimal envs
        pytest.skip("fastapi TestClient unavailable")

    async def fake_forward(self, payload, headers=None):  # type: ignore[no-untyped-def]
        assert payload["model"] == "z-ai/glm-5.2"
        return 200, {"content-type": "application/json"}, b'{"ok":true}'

    monkeypatch.setenv("NVIDIA_API_KEY_1", "k1")
    monkeypatch.setenv("NIM_PROXY_API_KEY", "nim-proxy-local")
    monkeypatch.setattr(NIMProxyService, "forward_non_stream", fake_forward)

    from _infra.nim_proxy import create_app

    client = TestClient(create_app())
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer nim-proxy-local"},
        json={"model": "z-ai/glm-5.2", "messages": [], "stream": False},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_forge_start_waits_for_smart_proxy_pid_and_health() -> None:
    source = Path("scripts/forge-start.sh").read_text(encoding="utf-8")

    assert "start_smart_proxy" in source
    assert "_infra/smart_proxy.py" in source
    assert "/_forge/health" in source
    assert "forge_smart_proxy.pid" in source
    assert "attempt ${attempt}/2" in source


def test_nim_proxy_defaults_fail_faster_than_upstream_five_minute_hang(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST", raising=False)
    monkeypatch.delenv("NIM_PROXY_READ_TIMEOUT_SECONDS", raising=False)

    settings = NIMProxySettings.from_env()

    assert settings.max_attempts_per_request == 1
    assert settings.read_timeout_seconds == 120.0


def test_smart_proxy_sidecar_route_avoids_nested_retries_and_autostarts_selector() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "nim_sidecar_route" in source
    assert "handles_retries=nim_sidecar_route" in source
    assert "stream_auto_continue" in source
    assert "1 + FORGE_AUTO_CONTINUE_MAX_ATTEMPTS" in source
    assert "await asyncio.to_thread(ensure_server, target_port)" in source
    assert "resp.status_code == 429 and is_remote and not handles_retries" in source



def test_smart_proxy_has_auto_continue_for_nim_sidecar_api_errors() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "FORGE_AUTO_CONTINUE_ON_API_ERROR" in source
    assert "FORGE_AUTO_CONTINUE_MAX_ATTEMPTS" in source
    assert "FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS" in source
    assert "FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS" in source
    assert "FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS" in source
    assert "FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS" in source
    assert "FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS" in source
    assert "auto-continue" in source
    assert "1 + FORGE_AUTO_CONTINUE_MAX_ATTEMPTS" in source
    assert "上下文接近超限，请新开会话" in source


def test_smart_proxy_auto_continue_uses_retry_after_without_short_cap() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "_auto_continue_wait_from_response" in source
    assert "cap=FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS" in source
    assert "_retry_after_seconds_from_error_payload" in source
    assert "FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS" in source
    assert "FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS" in source


def test_smart_proxy_auto_continue_has_no_output_and_partial_replay_guards() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS" in source
    assert "NoOutputTimeout" in source
    assert "_build_partial_continue_payload" in source
    assert "partial_replays" in source
    assert "FORGE_REQUEST_EVENT_LOG_PATH" in source


def test_smart_proxy_has_upstream_combined_token_guard() -> None:
    source = Path("_infra/smart_proxy.py").read_text(encoding="utf-8")

    assert "FORGE_UPSTREAM_COMBINED_LIMIT_TOKENS" in source
    assert "FORGE_UPSTREAM_COMBINED_SAFETY_TOKENS" in source
    assert "_apply_upstream_combined_budget" in source
    assert "_force_compact_messages_to_budget" in source
    assert "combined_budget" in source
    assert "保留 output max_tokens" in source
    assert "上下文接近超限，请新开会话" in source


def test_forward_non_stream_fallback_runs_even_with_one_attempt_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        async def no_sleep(_seconds: float) -> None:
            return None

        monkeypatch.setattr(asyncio, "sleep", no_sleep)
        fake = FakeClient(
            [
                httpx.Response(504, json={"error": "slow"}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        settings = _settings(enable_fallback=True, max_attempts_per_request=1)
        service = NIMProxyService(
            NIMKeyPool(["k1", "k2"], settings),
            settings,
            http_client=fake,  # type: ignore[arg-type]
        )

        status, _headers, body = await service.forward_non_stream(
            {"model": "z-ai/glm-5.2", "messages": [], "stream": False}
        )

        assert status == 200
        assert b"ok" in body
        assert fake.payloads[0]["model"] == "z-ai/glm-5.2"
        assert fake.payloads[1]["model"] == "deepseek-ai/DeepSeek-V4-Pro"
        assert service.fallback_count == 1

    asyncio.run(scenario())


def test_forward_non_stream_timeout_returns_504_without_hanging() -> None:
    class TimeoutClient:
        async def post(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise httpx.ReadTimeout("slow upstream")

    async def scenario() -> None:
        settings = _settings(max_attempts_per_request=1)
        service = NIMProxyService(
            NIMKeyPool(["k1"], settings),
            settings,
            http_client=TimeoutClient(),  # type: ignore[arg-type]
        )

        status, _headers, body = await service.forward_non_stream(
            {"model": "z-ai/glm-5.2", "messages": [], "stream": False}
        )

        assert status == 504
        assert b"ReadTimeout" in body
        assert service.retry_count == 1

    asyncio.run(scenario())



def test_forward_stream_timeout_is_serialized_as_sse_error() -> None:
    class RaisingStream:
        async def __aenter__(self):
            raise httpx.ReadTimeout("slow stream")

        async def __aexit__(self, *args):  # type: ignore[no-untyped-def]
            return False

    class TimeoutStreamClient:
        def stream(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return RaisingStream()

    async def scenario() -> None:
        settings = _settings(max_attempts_per_request=1)
        service = NIMProxyService(
            NIMKeyPool(["k1"], settings),
            settings,
            http_client=TimeoutStreamClient(),  # type: ignore[arg-type]
        )

        chunks = [chunk async for chunk in service.forward_stream(
            {"model": "z-ai/glm-5.2", "messages": [], "stream": True}
        )]
        body = b"".join(chunks)

        assert b"event: error" in body
        assert b"ReadTimeout" in body
        assert service.retry_count == 1
        assert service.stats()["pool"]["keys"][0]["error_count"] == 1

    asyncio.run(scenario())
