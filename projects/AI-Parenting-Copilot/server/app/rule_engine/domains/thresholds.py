# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Trend threshold rules with anti-alert-fatigue conditions."""

from __future__ import annotations

from server.app.rule_engine.domain.models import EvidenceItem, RuleInput, RuleResult, Verdict
from server.app.rule_engine.loader import RulePack


class ThresholdRuleModule:
    domain = "thresholds"

    def __init__(self, pack: RulePack) -> None:
        self.pack = pack
        self.rule_version = pack.version
        self.defaults = dict(pack.constants.get("defaults", {}))

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        payload = rule_input.payload
        source = str(payload.get("source", "manual"))
        requested_level = str(payload.get("requested_level", "yellow"))
        if source == "mmwave" and requested_level == "red":
            return RuleResult(
                domain=self.domain,
                verdict=Verdict.BLOCK,
                outputs={"alert_level": "blocked"},
                evidence=[
                    EvidenceItem(
                        rule_id="thresholds.mmwave_no_red_single_signal",
                        message="mmWave single signal must not produce red alert",
                        source=self.pack.source,
                    )
                ],
                rule_version=self.rule_version,
                reason_code="mmwave_no_red_single_signal",
            )

        consecutive_days = int(payload.get("consecutive_days", 0))
        deviation_percent = float(payload.get("deviation_percent", 0))
        required_days = int(self.defaults.get("consecutive_days", 2))
        required_deviation = float(self.defaults.get("deviation_percent", 20))
        matched = consecutive_days >= required_days and deviation_percent >= required_deviation
        return RuleResult(
            domain=self.domain,
            verdict=Verdict.ALERT if matched else Verdict.ALLOW,
            outputs={"alert_level": requested_level if matched else "none"},
            evidence=[
                EvidenceItem(
                    rule_id="thresholds.dual_condition",
                    message="Trend alert requires consecutive days and deviation threshold",
                    source=self.pack.source,
                    data={
                        "consecutive_days": consecutive_days,
                        "deviation_percent": deviation_percent,
                        "required_days": required_days,
                        "required_deviation": required_deviation,
                    },
                )
            ],
            rule_version=self.rule_version,
            reason_code="threshold_matched" if matched else "threshold_not_matched",
        )
