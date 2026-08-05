# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 12:10:00

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
