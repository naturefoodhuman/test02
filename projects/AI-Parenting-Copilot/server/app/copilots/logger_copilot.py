# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 23:00:00

"""P0 Logger Copilot.

Produces record candidates only; it does not write to DB or bypass user confirmation.
The deterministic parser is shared with Normalization so Quick Record and worker
behavior stay consistent for common P0 Chinese text inputs.
"""

from __future__ import annotations

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot
from server.app.normalization.parsers.voice import parse_voice_text


class LoggerCopilot:
    name = "logger"
    safety_level = "low"

    def can_handle(self, request: CopilotRequest) -> bool:
        return request.intent == "record"

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse:
        text = request.text.strip()
        candidate = self._parse(text)
        evidence: list[dict[str, object]] = [
            {
                "source": "logger_copilot.voice_parser",
                "message": "Record candidate parsed from user text",
                "memory_baby_id": memory.baby_id,
            }
        ]
        return CopilotResponse(
            copilot=self.name,
            intent=request.intent,
            payload={"record_candidate": candidate},
            evidence=evidence,
            requires_confirmation=True,
            safety_level=self.safety_level,
        )

    def _parse(self, text: str) -> dict[str, object]:
        record_type, payload, confidence = parse_voice_text(text)
        if record_type != "unknown":
            return {
                "event_type": record_type,
                "confidence": confidence,
                "normalized_payload": payload,
            }
        return {
            "event_type": "unknown",
            "confidence": confidence,
            "normalized_payload": payload,
        }
