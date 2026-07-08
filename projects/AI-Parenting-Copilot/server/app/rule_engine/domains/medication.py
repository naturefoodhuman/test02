# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Medication rule domain.

Dose numbers are produced only here, inside RuleResult.outputs, never by LLMs.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from server.app.common.clock import utc_now
from server.app.rule_engine.domain.models import EvidenceItem, RuleInput, RuleResult
from server.app.rule_engine.loader import RulePack


class MedicationRuleModule:
    domain = "medication"

    def __init__(self, pack: RulePack) -> None:
        self.pack = pack
        self.rule_version = pack.version
        self.medications: dict[str, dict[str, Any]] = dict(pack.constants.get("medications", {}))
        self.max_weight_age_days = int(pack.constants.get("max_weight_age_days", 14))

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        payload = rule_input.payload
        medication_key = str(payload.get("medication_key", "")).lower()
        medication = self.medications.get(medication_key)
        if medication is None:
            return self._block("unknown_medication", "Medication is not in the rule pack")

        age_months = payload.get("baby_age_months")
        if age_months is None:
            return self._block("age_required", "Baby age is required before medication advice")
        min_age = float(medication.get("min_age_months", 0))
        if float(age_months) < min_age:
            return self._block(
                "age_contraindication",
                f"{medication_key} is blocked below {min_age:g} months",
                {"baby_age_months": age_months, "min_age_months": min_age},
            )

        weight_kg = payload.get("weight_kg")
        if weight_kg is None:
            return self._block("weight_required", "Current weight is required; no dose is output")

        weight_measured_at = payload.get("weight_measured_at")
        if weight_measured_at:
            measured_at = datetime.fromisoformat(str(weight_measured_at))
            if utc_now() - measured_at > timedelta(days=self.max_weight_age_days):
                return self._block(
                    "weight_stale",
                    "Weight is too old; update weight before dose calculation",
                    {"max_weight_age_days": self.max_weight_age_days},
                )

        concentration = payload.get("concentration_mg_per_ml")
        if concentration is None:
            return self._block(
                "concentration_required",
                "Concentration is required; no ml dose is output",
            )

        min_interval = float(medication.get("min_interval_hours", 0))
        last_given_hours_ago = payload.get("last_given_hours_ago")
        if last_given_hours_ago is not None and float(last_given_hours_ago) < min_interval:
            return self._block(
                "interval_too_short",
                "Minimum medication interval has not elapsed",
                {"min_interval_hours": min_interval, "last_given_hours_ago": last_given_hours_ago},
            )

        max_doses = int(medication.get("max_doses_24h", 99))
        doses_24h = int(payload.get("doses_given_24h", 0))
        if doses_24h >= max_doses:
            return self._block(
                "daily_limit_reached",
                "24h dose count limit reached",
                {"max_doses_24h": max_doses, "doses_given_24h": doses_24h},
            )

        dose_mg_per_kg = float(medication["dose_mg_per_kg"])
        dose_mg = round(float(weight_kg) * dose_mg_per_kg, 3)
        dose_ml = round(dose_mg / float(concentration), 3)
        return RuleResult.allow(
            domain=self.domain,
            rule_version=self.rule_version,
            reason_code="dose_calculated_by_rule_engine",
            outputs={
                "medication_key": medication_key,
                "dose_mg": dose_mg,
                "dose_ml": dose_ml,
                "min_interval_hours": min_interval,
                "max_doses_24h": max_doses,
            },
            evidence=[
                EvidenceItem(
                    rule_id="medication.dose",
                    message="Dose calculated by MedicationRuleModule",
                    source=self.pack.source,
                    data={"dose_mg_per_kg": dose_mg_per_kg, "weight_kg": weight_kg},
                )
            ],
        )

    def _block(
        self,
        reason_code: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> RuleResult:
        return RuleResult.block(
            domain=self.domain,
            rule_version=self.rule_version,
            reason_code=reason_code,
            evidence=[
                EvidenceItem(
                    rule_id=f"medication.{reason_code}",
                    message=message,
                    source=self.pack.source,
                    data=data or {},
                )
            ],
        )
