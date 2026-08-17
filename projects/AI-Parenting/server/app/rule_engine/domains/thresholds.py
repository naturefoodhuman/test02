# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/domains/thresholds.py —— 告警阈值规则域（APC-T021）。
# 依据：ARCHITECTURE_FINAL §10.2（告警阈值规则：喂养/尿布/睡眠趋势"连续 N 天 / 偏离 X%"双条件）、
#       §13.2（mmWave 不单独触发红色医疗告警）、§14.1（告警等级）；
#       FINAL_PRD §12.3（黄色/橙色告警默认需"连续 N 天"或"偏离 X%"双条件，阈值可调；
#       趋势类避免单点触发）；
#       ENGINEERING_DESIGN §7.3；TASK_BACKLOG APC-T021。
# 设计：ThresholdRuleModule 实现 RuleModule Protocol（domain="thresholds")。
#       趋势双条件：连续 N 天偏离 X%（N 与 X 由规则包 YAML 配置，按 metric 取参数）。
#       单点异常不触发（PRD §12.3）；mmWave 单信号不得红色医疗告警（§13.2）。
#       输出 Alert candidate：alert_level + metric + deviation + days + evidence。
# 边界：只产出趋势告警候选（架构 §10.2），不做医疗诊断、不出剂量。
#       趋势类默认 yellow/orange，不单点强告警；mmWave 单信号最多 orange。

"""告警阈值规则域（APC-T021）。

``ThresholdRuleModule`` 实现 ``RuleModule`` Protocol（``domain="thresholds"``）。

趋势双条件（PRD §12.3）：黄色/橙色告警默认需 **连续 N 天** 且 **偏离 X%** 同时满足，
阈值由规则包 YAML 配置（每条 rule = 一个 metric，``conditions`` 匹配
``variables.metric``；``outputs`` 存 ``min_days``/``deviation_pct``/``alert_level``）。

求值链路：
    1. 取 metric 参数（规则包 YAML，按 ``variables.metric`` 匹配）。
    2. 校验 ``variables.consecutive_days >= min_days``（连续天数）。
    3. 校验 ``abs(variables.deviation_pct) >= deviation_pct``（偏离幅度）。
    4. 双条件同时满足 → 产出 Alert candidate（``alert_level`` + ``metric`` + ``deviation`` + ``days``）。
    5. 单点异常（consecutive_days=1 或 deviation 不足）→ ``info``，不触发（PRD §12.3）。
    6. mmWave 单信号（``variables.signal_source == "mmwave"``）→ 最多 ``orange``（§13.2）。

输出 Alert candidate（``outputs``）：``alert_level`` + ``metric`` + ``deviation_pct`` + ``consecutive_days`` + ``advice``。
``evidence`` 含 rule_id + policy_version + 文本（§15.4）。
"""

from __future__ import annotations

from typing import Any

from ..domain.models import (
    EvidenceRef,
    RuleContext,
    RuleDomain,
    RuleInput,
    RulePack,
    RuleResult,
)

# mmWave 单信号最高告警等级（§13.2）。
MMWAVE_MAX_LEVEL = "orange"


class ThresholdRuleModule:
    """告警阈值规则模块（APC-T021，domain="thresholds"）。

    趋势双条件参数从规则包 YAML 加载（每条 rule = 一个 metric）。``evaluate`` 按输入
    ``variables.metric`` 取参数，校验连续天数 + 偏离幅度双条件。规则包版本化（§13.2）。
    """

    domain: RuleDomain = "thresholds"

    def __init__(self, pack: RulePack) -> None:
        self._pack = pack
        self._rule_version = f"{pack.policy_type}@{pack.version}"
        self._params: dict[str, dict[str, Any]] = {}
        for rule in pack.rules:
            metric = _extract_metric_match(rule.conditions)
            if metric is not None:
                self._params[metric] = dict(rule.action.outputs)
                self._params[metric]["evidence_text"] = rule.action.evidence_text

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        """跑趋势双条件校验 → Alert candidate（单点异常不触发）。"""
        variables = input_.variables
        metric = variables.get("metric")
        if metric is None or metric not in self._params:
            return self._result("info", "unknown_metric", "未知指标，不触发趋势告警", [])

        params = self._params[metric]
        evidence_text = params.get("evidence_text", "")

        min_days = _as_int(params.get("min_days")) or 1
        deviation_threshold = _as_float(params.get("deviation_pct"))
        alert_level = str(params.get("alert_level", "yellow"))
        consecutive_days = _as_int(variables.get("consecutive_days")) or 0
        deviation_pct = _as_float(variables.get("deviation_pct")) or 0.0

        # 双条件：连续天数 + 偏离幅度同时满足（PRD §12.3）。
        days_ok = consecutive_days >= min_days
        dev_ok = deviation_threshold is not None and abs(deviation_pct) >= deviation_threshold
        if not (days_ok and dev_ok):
            return self._result(
                "info",
                "trend_not_met",
                "趋势双条件未满足，单点异常不触发（PRD §12.3）",
                [],
                outputs={
                    "metric": metric,
                    "consecutive_days": consecutive_days,
                    "deviation_pct": deviation_pct,
                },
            )

        # mmWave 单信号不得红色医疗告警（§13.2）。
        if variables.get("signal_source") == "mmwave" and alert_level == "red":
            alert_level = MMWAVE_MAX_LEVEL
            evidence_text = "mmWave 单信号不触发红色医疗告警，降级为橙色（§13.2）"

        outputs: dict[str, Any] = {
            "alert_level": alert_level,
            "metric": metric,
            "deviation_pct": deviation_pct,
            "consecutive_days": consecutive_days,
            "advice": _advice_for(alert_level),
        }
        return self._result(
            _verdict_for(alert_level),
            "trend_alert",
            evidence_text
            or f"{metric} 趋势双条件命中（连续 {consecutive_days} 天，偏离 {deviation_pct}%）",
            [
                EvidenceRef(
                    rule_id="thresholds", policy_version=ctx.policy_version, text=evidence_text
                )
            ],
            outputs=outputs,
        )

    def _result(
        self,
        verdict: str,
        reason_code: str,
        message: str,
        evidence: list[EvidenceRef],
        outputs: dict[str, Any] | None = None,
    ) -> RuleResult:
        return RuleResult(
            verdict=verdict,  # type: ignore[arg-type]
            outputs=outputs or {},
            evidence=evidence,
            rule_version=self._rule_version,
            reason_code=reason_code,
        )


# ---- 辅助 ----


def _extract_metric_match(conditions: list) -> str | None:
    """从 rule.conditions 取 variables.metric 的 eq 匹配值。"""
    for cond in conditions:
        if cond.op == "eq" and cond.field == "variables.metric":
            return str(cond.value)
    return None


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _verdict_for(level: str) -> str:
    if level == "red":
        return "block"
    if level in ("orange", "yellow"):
        return "warn"
    return "info"


def _advice_for(level: str) -> str:
    if level == "red":
        return "立即关注并就医评估"
    if level == "orange":
        return "24h 内关注并咨询医生"
    if level == "yellow":
        return "关注趋势，必要时咨询医生"
    return "继续观察"


__all__ = ["MMWAVE_MAX_LEVEL", "ThresholdRuleModule"]
