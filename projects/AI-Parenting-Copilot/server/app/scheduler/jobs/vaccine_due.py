# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Vaccine due reminder job."""

from __future__ import annotations

from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.vaccine import VaccineRuleModule


class VaccineDueJob:
    name = "vaccine_due"

    def __init__(self, module: VaccineRuleModule, payload: dict[str, object]) -> None:
        self.module = module
        self.payload = payload

    async def run(self) -> dict[str, object]:
        result = self.module.evaluate(RuleInput(domain="vaccine", payload=self.payload))
        due = [
            item
            for item in result.outputs.get("planned", [])
            if item.get("status") in {"due", "overdue"}
        ]
        return {
            "kind": "vaccine_due",
            "count": len(due),
            "items": due,
            "alert_level": "blue" if due else None,
        }
