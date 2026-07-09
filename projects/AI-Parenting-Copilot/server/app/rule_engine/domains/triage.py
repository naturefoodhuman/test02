# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Triage red-line rule domain."""

from __future__ import annotations

from server.app.rule_engine.domain.models import EvidenceItem, RuleInput, RuleResult, Verdict
from server.app.rule_engine.loader import RulePack


class TriageRuleModule:
    domain = "triage"

    def __init__(self, pack: RulePack) -> None:
        self.pack = pack
        self.rule_version = pack.version
        self.redline_age_months = float(pack.constants.get("redline_age_months", 3))
        self.redline_temperature_c = float(pack.constants.get("redline_temperature_c", 38.0))
        self.danger_signals = set(pack.constants.get("danger_signals", []))

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        payload = rule_input.payload
        age_months = payload.get("baby_age_months")
        temperature_c = payload.get("temperature_c")
        signals = set(payload.get("danger_signals", []) or [])
        evidence: list[EvidenceItem] = []

        if (
            age_months is not None
            and temperature_c is not None
            and float(age_months) < self.redline_age_months
            and float(temperature_c) >= self.redline_temperature_c
        ):
            evidence.append(
                EvidenceItem(
                    rule_id="triage.young_infant_fever_redline",
                    message="Baby under 3 months with temperature >= 38°C is a red triage line",
                    source=self.pack.source,
                    data={"age_months": age_months, "temperature_c": temperature_c},
                )
            )
            return RuleResult(
                domain=self.domain,
                verdict=Verdict.ALERT,
                outputs={"alert_level": "red", "recommended_action": "seek_medical_care_now"},
                evidence=evidence,
                rule_version=self.rule_version,
                reason_code="young_infant_fever_redline",
            )

        matched = sorted(signals & self.danger_signals)
        if matched:
            evidence.append(
                EvidenceItem(
                    rule_id="triage.danger_signal",
                    message="Danger signal matched triage rule pack",
                    source=self.pack.source,
                    data={"danger_signals": matched},
                )
            )
            return RuleResult(
                domain=self.domain,
                verdict=Verdict.ALERT,
                outputs={"alert_level": "orange", "matched_signals": matched},
                evidence=evidence,
                rule_version=self.rule_version,
                reason_code="danger_signal",
            )

        return RuleResult.allow(
            domain=self.domain,
            rule_version=self.rule_version,
            reason_code="no_redline_matched",
            outputs={"alert_level": "none"},
            evidence=[
                EvidenceItem(
                    rule_id="triage.no_redline_matched",
                    message="No redline triage rule matched",
                    source=self.pack.source,
                )
            ],
        )
