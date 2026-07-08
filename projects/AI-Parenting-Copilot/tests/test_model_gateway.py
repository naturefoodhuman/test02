# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 23:55:00


"""APC-T024 tests for Model Gateway routing and client behavior."""
from __future__ import annotations

import httpx
import pytest

from server.app.model_gateway import (
    FakeModelClient,
    ModelGatewayClient,
    ModelMessage,
    ModelRequest,
    load_routing_config,
)
from server.app.settings import Settings


def test_routing_config_loads_default_plan() -> None:
    routing = load_routing_config()
    key, plan = routing.resolve(None)

    assert key == "parenting-local-first"
    assert plan.provider == "smart_proxy"
    assert plan.allow_cloud_fallback is False


@pytest.mark.asyncio
async def test_model_gateway_client_posts_anthropic_compatible_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["routing_plan"] = request.headers["x-routing-plan"]
        captured["payload"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "model": "unit-model",
                "content": [{"type": "text", "text": "hello"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = ModelGatewayClient(settings=Settings(env="test"), http_client=http_client)
        response = await client.complete(
            ModelRequest(messages=[ModelMessage(role="user", content="hi")])
        )

    assert response.text == "hello"
    assert response.model == "unit-model"
    assert captured["url"] == "http://127.0.0.1:4000/v1/messages"
    assert captured["routing_plan"] == "parenting-local-first"
    assert '"messages"' in str(captured["payload"])


@pytest.mark.asyncio
async def test_fake_model_client_records_requests() -> None:
    fake = FakeModelClient(["first", "second"])

    first = await fake.complete(ModelRequest(messages=[ModelMessage(role="user", content="one")]))
    second = await fake.complete(ModelRequest(messages=[ModelMessage(role="user", content="two")]))

    assert first.text == "first"
    assert second.text == "second"
    assert len(fake.requests) == 2


@pytest.mark.asyncio
async def test_model_gateway_client_supports_vision_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = request.read().decode()
        return httpx.Response(200, json={"content": [{"type": "text", "text": "seen"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = ModelGatewayClient(settings=Settings(env="test"), http_client=http_client)
        response = await client.vision(image_base64="ZmFrZQ==", prompt="describe")

    assert response.text == "seen"
    assert '"type":"image"' in str(captured["payload"]).replace(" ", "")
    assert '"data":"ZmFrZQ=="' in str(captured["payload"]).replace(" ", "")
