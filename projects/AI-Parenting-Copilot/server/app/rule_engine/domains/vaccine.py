# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 03:35:00


"""Vaccine planning rule domain.

The P0 implementation is deterministic and schedule-driven. It produces structured
due-date/status outputs for Scheduler/Copilots; it does not make clinical decisions.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from server.app.rule_engine.domain.models import EvidenceItem, RuleInput, RuleResult, Verdict
from server.app.rule_engine.loader import RulePack


def _to_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value)).date()


class VaccineRuleModule:
    domain = "vaccine"

    def __init__(self, pack: RulePack) -> None:
        self.pack = pack
        self.rule_version = pack.version
        self.schedule: list[dict[str, Any]] = list(pack.constants.get("schedule", []))
        self.default_grace_days = int(pack.constants.get("default_grace_days", 7))

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        payload = rule_input.payload
        birth_date_value = payload.get("birth_date")
        if birth_date_value is None:
            return RuleResult.block(
                domain=self.domain,
                rule_version=self.rule_version,
                reason_code="birth_date_required",
                evidence=[
                    EvidenceItem(
                        rule_id="vaccine.birth_date_required",
                        message="birth_date is required to generate vaccine plan",
                        source=self.pack.source,
                    )
                ],
            )
        birth_date = _to_date(birth_date_value)
        as_of = _to_date(payload.get("as_of", date.today().isoformat()))
        record_index = {
            str(record.get("vaccine_key")): str(record.get("status", "planned"))
            for record in list(payload.get("records", []) or [])
        }
        planned: list[dict[str, Any]] = []
        evidence: list[EvidenceItem] = []
        for item in self.schedule:
            vaccine_key = str(item["vaccine_key"])
            due_date = birth_date + timedelta(days=int(item.get("due_day", 0)))
            grace_days = int(item.get("grace_days", self.default_grace_days))
            status = self._status_for(
                vaccine_key=vaccine_key,
                due_date=due_date,
                as_of=as_of,
                grace_days=grace_days,
                record_status=record_index.get(vaccine_key),
            )
            planned.append(
                {
                    "vaccine_key": vaccine_key,
                    "label": item.get("label", vaccine_key),
                    "dose": item.get("dose"),
                    "due_date": due_date.isoformat(),
                    "status": status,
                    "grace_days": grace_days,
                }
            )
            evidence.append(
                EvidenceItem(
                    rule_id=f"vaccine.{vaccine_key}",
                    message="Vaccine schedule item evaluated",
                    source=self.pack.source,
                    data={"due_date": due_date.isoformat(), "status": status},
                )
            )
        return RuleResult(
            domain=self.domain,
            verdict=Verdict.ALLOW,
            outputs={"region": payload.get("vaccine_region", "CN"), "planned": planned},
            evidence=evidence,
            rule_version=self.rule_version,
            reason_code="vaccine_plan_generated",
        )

    @staticmethod
    def _status_for(
        *,
        vaccine_key: str,
        due_date: date,
        as_of: date,
        grace_days: int,
        record_status: str | None,
    ) -> str:
        if record_status in {"completed", "skipped", "delayed"}:
            return record_status
        if as_of > due_date + timedelta(days=grace_days):
            return "overdue"
        if as_of >= due_date:
            return "due"
        return "planned"
