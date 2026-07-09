# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 03:35:00


"""Growth percentile rule domain with simplified WHO-compatible fixture tables."""

from __future__ import annotations

from typing import Any

from server.app.rule_engine.domain.models import EvidenceItem, RuleInput, RuleResult, Verdict
from server.app.rule_engine.loader import RulePack


class GrowthRuleModule:
    domain = "growth"

    def __init__(self, pack: RulePack) -> None:
        self.pack = pack
        self.rule_version = pack.version
        self.tables: dict[str, Any] = dict(pack.constants.get("tables", {}))

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        payload = rule_input.payload
        sex = str(payload.get("sex", "")).lower()
        metric = str(payload.get("metric", "weight_kg"))
        value = payload.get("value")
        age_months = payload.get("age_months")
        if not sex or value is None or age_months is None:
            return RuleResult.block(
                domain=self.domain,
                rule_version=self.rule_version,
                reason_code="growth_required_fields_missing",
                evidence=[
                    EvidenceItem(
                        rule_id="growth.required_fields",
                        message="sex, age_months and value are required",
                        source=self.pack.source,
                    )
                ],
            )
        table = self._nearest_table(sex=sex, metric=metric, age_months=float(age_months))
        percentile = self._percentile_band(float(value), table)
        trend = self._trend_notice(payload)
        return RuleResult(
            domain=self.domain,
            verdict=Verdict.ALLOW,
            outputs={
                "metric": metric,
                "sex": sex,
                "age_months": age_months,
                "value": value,
                "percentile_band": percentile,
                "alert_level": "none",
                "trend_notice": trend,
            },
            evidence=[
                EvidenceItem(
                    rule_id="growth.percentile_fixture",
                    message="Percentile estimated from simplified WHO-compatible fixture table",
                    source=self.pack.source,
                    data={"table": table},
                )
            ],
            rule_version=self.rule_version,
            reason_code="growth_percentile_estimated",
        )

    def _nearest_table(self, *, sex: str, metric: str, age_months: float) -> dict[str, float]:
        sex_tables = self.tables.get(sex)
        if not sex_tables:
            raise ValueError(f"unsupported sex: {sex}")
        metric_tables = sex_tables.get(metric)
        if not metric_tables:
            raise ValueError(f"unsupported metric: {metric}")
        nearest_key = min(metric_tables, key=lambda key: abs(float(key) - age_months))
        return {k: float(v) for k, v in metric_tables[nearest_key].items()}

    @staticmethod
    def _percentile_band(value: float, table: dict[str, float]) -> str:
        ordered = [
            (int(key[1:]), threshold) for key, threshold in table.items() if key.startswith("p")
        ]
        ordered.sort(key=lambda item: item[0])
        if value < ordered[0][1]:
            return "below_p3"
        for percentile, threshold in ordered:
            if value <= threshold:
                return f"p{percentile}"
        return "above_p97"

    @staticmethod
    def _trend_notice(payload: dict[str, Any]) -> str | None:
        previous = payload.get("previous_percentile_band")
        current = payload.get("current_percentile_band")
        if previous and current and previous != current:
            return "percentile_band_changed_review_trend"
        return None
