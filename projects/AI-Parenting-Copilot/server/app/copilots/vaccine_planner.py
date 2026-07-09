# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:10:00


"""P0 Vaccine Planner Copilot wrapper over Rule Engine."""

from __future__ import annotations

from pathlib import Path

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot
from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.vaccine import VaccineRuleModule
from server.app.rule_engine.loader import load_rule_pack


class VaccinePlannerCopilot:
    name = "vaccine_planner"
    safety_level = "medium"

    def __init__(self, module: VaccineRuleModule | None = None) -> None:
        self.module = module or VaccineRuleModule(
            load_rule_pack(Path("config/rules/vaccine/cn-nip-2024.yaml"))
        )

    def can_handle(self, request: CopilotRequest) -> bool:
        return request.intent == "vaccine"

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse:
        raw_rule_input = request.context.get("rule_input", {})
        payload = dict(raw_rule_input) if isinstance(raw_rule_input, dict) else {}
        if "birth_date" not in payload:
            payload["birth_date"] = memory.hard_facts.get("birth_date")
        if "vaccine_region" not in payload:
            payload["vaccine_region"] = memory.hard_facts.get("vaccine_region", "CN")
        result = self.module.evaluate(RuleInput(domain="vaccine", payload=payload))
        return CopilotResponse(
            copilot=self.name,
            intent=request.intent,
            payload={"rule_result": result.model_dump(mode="json")},
            evidence=[item.model_dump(mode="json") for item in result.evidence],
            requires_confirmation=False,
            safety_level=self.safety_level,
        )
