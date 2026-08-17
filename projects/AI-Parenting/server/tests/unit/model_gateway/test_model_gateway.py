# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""Model Gateway 单元测试（APC-T024）。

覆盖：routing plan 解析、FakeModelClient、SmartProxyModelClient（httpx mock）的
chat/vision/timeout/fallback/非 2xx。不依赖真实 Smart Proxy（CI 禁调真实模型）。
asyncio_mode=auto。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from server.app.model_gateway.client import (
    CHAT_TIMEOUT,
    VISION_TIMEOUT,
    FakeModelClient,
    ModelError,
    SmartProxyModelClient,
)
from server.app.model_gateway.domain import RoutingPlan
from server.app.model_gateway.routing import get_plan, load_plans

CONFIG_DIR = Path(__file__).resolve().parents[4] / "config"
ROUTING_PLANS = CONFIG_DIR / "routing_plans.yaml"


# ---- routing plan 解析 ----


def test_load_plans_parses_keys():
    plans = load_plans(ROUTING_PLANS)
    assert "copilot.triage" in plans
    assert "vision.jaundice" in plans
    triage = plans["copilot.triage"]
    assert isinstance(triage, RoutingPlan)
    assert triage.model == "mtplx-qwen36-27b"
    assert triage.is_vision is False
    assert triage.max_tokens == 1024


def test_load_plans_vision_flag():
    plans = load_plans(ROUTING_PLANS)
    jaundice = plans["vision.jaundice"]
    assert jaundice.is_vision is True


def test_get_plan_missing_raises_keyerror():
    plans = load_plans(ROUTING_PLANS)
    with pytest.raises(KeyError, match="routing plan not found"):
        get_plan(plans, "nonexistent.plan")


def test_load_plans_missing_file_empty():
    plans = load_plans(Path("/nonexistent/routing_plans.yaml"))
    assert plans == {}


# ---- FakeModelClient ----


async def test_fake_client_chat_returns_placeholder():
    c = FakeModelClient()
    r = await c.chat("copilot.triage", [{"role": "user", "content": "hi"}])
    assert r.plan == "copilot.triage"
    assert "copilot.triage" in r.content
    assert r.model == "fake-model"
    assert r.usage["output_tokens"] == 1


async def test_fake_client_chat_custom_response():
    c = FakeModelClient(responses={"copilot.triage": "分诊建议：观察体温"})
    r = await c.chat("copilot.triage", [{"role": "user", "content": "38.5度"}])
    assert r.content == "分诊建议：观察体温"


async def test_fake_client_vision_records_call():
    c = FakeModelClient()
    r = await c.vision("vision.jaundice", b"\x89PNG fake", "评估黄疸")
    assert "vision.jaundice" in r.content
    assert c.calls[-1][0] == "vision"
    assert c.calls[-1][1] == "vision.jaundice"
    assert c.calls[-1][2]["image_bytes"] == 9


async def test_fake_client_chat_records_tools():
    c = FakeModelClient()
    tools = [{"name": "lookup_rule", "input_schema": {}}]
    await c.chat("copilot.triage", [{"role": "user", "content": "hi"}], tools=tools)
    assert c.calls[-1][2]["tools"] == tools


# ---- SmartProxyModelClient（httpx mock）----


def _mock_client(
    handler: Any, plans: dict[str, RoutingPlan] | None = None
) -> SmartProxyModelClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="http://127.0.0.1:4000", transport=transport)
    if plans is None:
        plans = {
            "copilot.triage": RoutingPlan(
                key="copilot.triage", model="mtplx-qwen36-27b", max_tokens=1024
            ),
            "vision.jaundice": RoutingPlan(
                key="vision.jaundice", model="mtplx-qwen36-27b", max_tokens=512, is_vision=True
            ),
        }
    return SmartProxyModelClient(base_url="http://127.0.0.1:4000", plans=plans, client=http)


async def test_smart_proxy_chat_success():
    def handler(req: httpx.Request) -> httpx.Response:
        body = req.read()
        import json

        data = json.loads(body)
        assert data["model"] == "mtplx-qwen36-27b"
        assert data["max_tokens"] == 1024
        assert data["messages"] == [{"role": "user", "content": "hi"}]
        return httpx.Response(
            200,
            json={
                "model": "mtplx-qwen36-27b",
                "content": [{"type": "text", "text": "你好"}],
                "usage": {"input_tokens": 5, "output_tokens": 2},
            },
        )

    c = _mock_client(handler)
    r = await c.chat("copilot.triage", [{"role": "user", "content": "hi"}])
    assert r.content == "你好"
    assert r.model == "mtplx-qwen36-27b"
    assert r.plan == "copilot.triage"
    assert r.usage == {"input_tokens": 5, "output_tokens": 2}


async def test_smart_proxy_chat_timeout():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("simulated")

    c = _mock_client(handler)
    with pytest.raises(ModelError, match="timeout"):
        await c.chat("copilot.triage", [{"role": "user", "content": "hi"}])


async def test_smart_proxy_chat_http_error():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated")

    c = _mock_client(handler)
    with pytest.raises(ModelError, match="request error"):
        await c.chat("copilot.triage", [{"role": "user", "content": "hi"}])


async def test_smart_proxy_chat_non_2xx():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream error")

    c = _mock_client(handler)
    with pytest.raises(ModelError, match="status=500"):
        await c.chat("copilot.triage", [{"role": "user", "content": "hi"}])


async def test_smart_proxy_vision_success():
    def handler(req: httpx.Request) -> httpx.Response:
        body = req.read()
        import json

        data = json.loads(body)
        # vision 消息含 image + text block。
        content = data["messages"][0]["content"]
        assert any(b.get("type") == "image" for b in content)
        assert any(b.get("type") == "text" and "评估" in b.get("text", "") for b in content)
        return httpx.Response(
            200,
            json={
                "model": "mtplx-qwen36-27b",
                "content": [{"type": "text", "text": "未见明显黄疸"}],
            },
        )

    c = _mock_client(handler)
    r = await c.vision("vision.jaundice", b"\xff\xd8\xff fake jpeg", "评估黄疸")
    assert r.content == "未见明显黄疸"
    assert r.plan == "vision.jaundice"


async def test_smart_proxy_chat_vision_plan_rejected():
    """chat 调用 vision-only plan → ModelError（防御性）。"""
    c = _mock_client(lambda req: httpx.Response(200, json={}))
    with pytest.raises(ModelError, match="vision-only"):
        await c.chat("vision.jaundice", [{"role": "user", "content": "hi"}])


async def test_smart_proxy_chat_missing_plan_keyerror():
    c = _mock_client(lambda req: httpx.Response(200, json={}))
    with pytest.raises(KeyError, match="routing plan not found"):
        await c.chat("nonexistent.plan", [{"role": "user", "content": "hi"}])


def test_timeouts_match_spec():
    """文本 30s，视觉 60s（APC-T024 规格）。"""
    assert CHAT_TIMEOUT == 30.0
    assert VISION_TIMEOUT == 60.0
