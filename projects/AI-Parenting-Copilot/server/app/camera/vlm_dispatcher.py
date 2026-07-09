# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:55:00


"""VLM dispatcher shadow wrapper that only uses injected Model Gateway client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class VisionClient(Protocol):
    async def vision(
        self,
        *,
        image_base64: str,
        prompt: str,
        media_type: str = "image/jpeg",
        plan_key: str | None = None,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class VLMShadowResult:
    mode: str
    dispatched: bool
    response_text: str | None = None


class VLMDispatcher:
    def __init__(
        self,
        model_client: VisionClient | None = None,
        *,
        shadow_mode: bool = True,
    ) -> None:
        self.model_client = model_client
        self.shadow_mode = shadow_mode

    async def dispatch(self, *, image_base64: str, prompt: str) -> VLMShadowResult:
        if self.model_client is None:
            return VLMShadowResult(mode="shadow", dispatched=False)
        response = await self.model_client.vision(image_base64=image_base64, prompt=prompt)
        return VLMShadowResult(
            mode="shadow" if self.shadow_mode else "active",
            dispatched=True,
            response_text=str(getattr(response, "text", "")),
        )
