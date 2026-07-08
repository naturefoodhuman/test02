# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 23:55:00


"""Smart Proxy client for Anthropic-compatible model calls."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from server.app.common.errors import AppError
from server.app.model_gateway.routing import RoutingConfig, load_routing_config
from server.app.settings import Settings, get_settings

Role = Literal["system", "user", "assistant"]


class ModelGatewayError(AppError):
    """Raised when the model gateway request fails."""

    status_code = 502
    code = "MODEL_GATEWAY_ERROR"


class ModelMessage(BaseModel):
    """Chat-style model message."""

    role: Role
    content: str


class ModelRequest(BaseModel):
    """Model completion request."""

    messages: list[ModelMessage]
    plan_key: str | None = None
    system: str | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Normalized model response."""

    text: str
    model: str | None = None
    provider: str = "smart_proxy"
    plan_key: str
    raw: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] | None = None


def _extract_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "".join(parts)
    if isinstance(content, str):
        return content
    completion = payload.get("completion")
    if isinstance(completion, str):
        return completion
    message = payload.get("message")
    if isinstance(message, str):
        return message
    return ""


class ModelGatewayClient:
    """Thin client over the factory Smart Proxy at port 4000."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        routing: RoutingConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.routing = routing or load_routing_config()
        self._http_client = http_client

    async def _post_payload(
        self,
        *,
        plan_key: str,
        provider: str,
        safety_profile: str,
        url: str,
        payload: dict[str, Any],
    ) -> ModelResponse:
        headers = {
            "content-type": "application/json",
            "x-routing-plan": plan_key,
            "x-safety-profile": safety_profile,
        }
        client = self._http_client or httpx.AsyncClient(
            timeout=self.settings.model_gateway.timeout_seconds
        )
        close_after = self._http_client is None
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            raw = response.json()
        except Exception as exc:
            raise ModelGatewayError(
                "Model gateway request failed",
                evidence={"plan_key": plan_key, "url": url, "error": type(exc).__name__},
            ) from exc
        finally:
            if close_after:
                await client.aclose()
        return ModelResponse(
            text=_extract_text(raw),
            model=raw.get("model", payload.get("model")),
            provider=provider,
            plan_key=plan_key,
            raw=raw,
            usage=raw.get("usage") if isinstance(raw.get("usage"), dict) else None,
        )

    def _resolve_endpoint(self, plan_key: str | None) -> tuple[str, Any, str]:
        resolved_key, plan = self.routing.resolve(plan_key)
        base_url = str(plan.base_url or self.settings.model_gateway.base_url).rstrip("/")
        endpoint = plan.endpoint if plan.endpoint.startswith("/") else f"/{plan.endpoint}"
        return resolved_key, plan, f"{base_url}{endpoint}"

    async def complete(self, request: ModelRequest) -> ModelResponse:
        """Send an Anthropic-compatible `/v1/messages` request through Smart Proxy."""

        plan_key, plan, url = self._resolve_endpoint(request.plan_key)
        payload = {
            "model": plan.model,
            "max_tokens": request.max_tokens or plan.max_tokens,
            "temperature": (
                request.temperature if request.temperature is not None else plan.temperature
            ),
            "messages": [
                msg.model_dump()
                for msg in request.messages
                if msg.role in {"user", "assistant"}
            ],
            "metadata": {**request.metadata, "routing_plan": plan_key},
        }
        system = request.system or next(
            (msg.content for msg in request.messages if msg.role == "system"),
            None,
        )
        if system:
            payload["system"] = system
        return await self._post_payload(
            plan_key=plan_key,
            provider=plan.provider,
            safety_profile=plan.safety_profile,
            url=url,
            payload=payload,
        )

    async def chat(
        self,
        messages: Sequence[ModelMessage],
        *,
        plan_key: str | None = None,
    ) -> ModelResponse:
        """Convenience chat API required by downstream copilots."""

        return await self.complete(ModelRequest(messages=list(messages), plan_key=plan_key))

    async def vision(
        self,
        *,
        image_base64: str,
        prompt: str,
        media_type: str = "image/jpeg",
        plan_key: str | None = None,
    ) -> ModelResponse:
        """Send an Anthropic-compatible image + prompt request through Smart Proxy."""

        resolved_key, plan, url = self._resolve_endpoint(plan_key)
        payload = {
            "model": plan.model,
            "max_tokens": plan.max_tokens,
            "temperature": plan.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "metadata": {"routing_plan": resolved_key, "input_kind": "vision"},
        }
        return await self._post_payload(
            plan_key=resolved_key,
            provider=plan.provider,
            safety_profile=plan.safety_profile,
            url=url,
            payload=payload,
        )


class FakeModelClient:
    """Deterministic test double used in CI and downstream module tests."""

    def __init__(self, responses: Sequence[str] | None = None) -> None:
        self.responses = list(responses or ["ok"])
        self.requests: list[ModelRequest] = []

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        index = min(len(self.requests) - 1, len(self.responses) - 1)
        return ModelResponse(
            text=self.responses[index],
            model="fake",
            provider="fake",
            plan_key="fake",
        )
