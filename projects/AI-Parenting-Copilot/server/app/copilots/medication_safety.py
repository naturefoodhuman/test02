# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:10:00


"""P0 Medication Basic Copilot wrapper.

It only delegates dose/interval checks to Rule Engine and returns structured output.
"""

from __future__ import annotations

from pathlib import Path

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot
from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.medication import MedicationRuleModule
from server.app.rule_engine.loader import load_rule_pack

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MedicationSafetyCopilot:
    name = "medication_safety"
    safety_level = "high"

    def __init__(self, module: MedicationRuleModule | None = None) -> None:
        self._module = module

    @property
    def module(self) -> MedicationRuleModule:
        if self._module is None:
            self._module = MedicationRuleModule(
                load_rule_pack(PROJECT_ROOT / "config/rules/medication/base.yaml")
            )
        return self._module

    def can_handle(self, request: CopilotRequest) -> bool:
        return request.intent == "medication"

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse:
        raw_rule_input = request.context.get("rule_input", {})
        payload = dict(raw_rule_input) if isinstance(raw_rule_input, dict) else {}
        payload.setdefault("weight_kg", memory.hard_facts.get("weight_kg"))
        payload.setdefault("baby_age_months", memory.hard_facts.get("age_months"))
        result = self.module.evaluate(RuleInput(domain="medication", payload=payload))
        return CopilotResponse(
            copilot=self.name,
            intent=request.intent,
            payload={"rule_result": result.model_dump(mode="json"), "source": "rule_engine"},
            evidence=[item.model_dump(mode="json") for item in result.evidence],
            requires_confirmation=True,
            safety_level=self.safety_level,
        )
