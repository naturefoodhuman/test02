# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:10:00


"""P0 Growth & Milestone Copilot wrapper over GrowthRuleModule."""

from __future__ import annotations

from pathlib import Path

from server.app.copilots.base import CopilotRequest, CopilotResponse
from server.app.memory.injector import MemorySnapshot
from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.growth import GrowthRuleModule
from server.app.rule_engine.loader import load_rule_pack


class GrowthMilestoneCopilot:
    name = "growth_milestone"
    safety_level = "low"

    def __init__(self, module: GrowthRuleModule | None = None) -> None:
        self.module = module or GrowthRuleModule(
            load_rule_pack(Path("config/rules/growth/who-0-5.yaml"))
        )

    def can_handle(self, request: CopilotRequest) -> bool:
        return request.intent == "growth"

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse:
        raw_rule_input = request.context.get("rule_input", {})
        payload = dict(raw_rule_input) if isinstance(raw_rule_input, dict) else {}
        payload.setdefault("sex", memory.hard_facts.get("sex"))
        payload.setdefault("age_months", memory.hard_facts.get("age_months"))
        result = self.module.evaluate(RuleInput(domain="growth", payload=payload))
        return CopilotResponse(
            copilot=self.name,
            intent=request.intent,
            payload={"rule_result": result.model_dump(mode="json")},
            evidence=[item.model_dump(mode="json") for item in result.evidence],
            requires_confirmation=False,
            safety_level=self.safety_level,
        )
