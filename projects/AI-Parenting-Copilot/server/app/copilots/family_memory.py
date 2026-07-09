# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:10:00


"""P0 Family Memory Copilot shell.

Produces structured memory_update candidates only. Persistence and audit are done by
future Memory/Repository services.
"""

from __future__ import annotations

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot


class FamilyMemoryCopilot:
    name = "family_memory"
    safety_level = "low"

    def can_handle(self, request: CopilotRequest) -> bool:
        return request.intent == "family_memory"

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse:
        key = str(request.context.get("key", "note"))
        value = request.context.get("value", request.text)
        return CopilotResponse(
            copilot=self.name,
            intent=request.intent,
            payload={
                "memory_update": {
                    "family_id": request.family_id or memory.family_id,
                    "key": key,
                    "value": value,
                }
            },
            evidence=[{"source": "family_memory_copilot", "message": "Memory update candidate"}],
            requires_confirmation=True,
            safety_level=self.safety_level,
        )
