# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""P0 Logger Copilot.

Produces record candidates only; it does not write to DB or bypass user confirmation.
"""

from __future__ import annotations

import re

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot

FEEDING_RE = re.compile(r"(?:喂|喝|奶).*?(?P<amount>\d+(?:\.\d+)?)\s*(?:ml|毫升)", re.I)
TEMP_RE = re.compile(r"(?P<temp>\d{2}(?:\.\d)?)\s*(?:度|℃|c)", re.I)
DIAPER_RE = re.compile(r"(尿布|纸尿裤|便便|大便|尿)")


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
                "source": "logger_copilot.regex",
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
        feeding = FEEDING_RE.search(text)
        if feeding:
            return {
                "event_type": "feeding",
                "confidence": 0.92,
                "normalized_payload": {"amount_ml": float(feeding.group("amount"))},
            }
        temp = TEMP_RE.search(text)
        if temp:
            return {
                "event_type": "temperature",
                "confidence": 0.88,
                "normalized_payload": {"value_c": float(temp.group("temp"))},
            }
        if DIAPER_RE.search(text):
            return {
                "event_type": "diaper",
                "confidence": 0.75,
                "normalized_payload": {"note": text},
            }
        return {
            "event_type": "unknown",
            "confidence": 0.2,
            "normalized_payload": {"raw_text": text},
        }
