# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:10:00


"""P0 Proactive Copilot shell.

It returns reminder candidates and never generates alert levels by itself.
"""

from __future__ import annotations

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot


class ProactiveCopilot:
    name = "proactive"
    safety_level = "low"

    def can_handle(self, request: CopilotRequest) -> bool:
        return request.intent == "proactive"

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse:
        reminders = []
        if memory.short_context.get("last_feeding_minutes") is not None:
            reminders.append(
                {
                    "kind": "feeding_interval",
                    "message": "Review feeding interval in Today page",
                    "alert_level": None,
                }
            )
        if not reminders:
            reminders.append(
                {
                    "kind": "daily_summary",
                    "message": "No proactive reminder",
                    "alert_level": None,
                }
            )
        return CopilotResponse(
            copilot=self.name,
            intent=request.intent,
            payload={"reminder_candidates": reminders},
            evidence=[{"source": "proactive_copilot", "message": "No alert level generated"}],
            requires_confirmation=False,
            safety_level=self.safety_level,
        )
