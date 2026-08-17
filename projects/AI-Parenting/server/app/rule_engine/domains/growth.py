# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/domains/growth.py —— 生长规则域（APC-T023）。
# 依据：ARCHITECTURE_FINAL §10.2（生长规则：WHO 0–5 岁百分位、按性别、趋势提醒）；
#       FINAL_PRD §11.13（成长曲线 P0：体重/身长/头围 + WHO 百分位 + 0~5 岁 + 按性别 +
#       近 30 天趋势 + 与出生数据对比 + 百分位异常变化提醒；限制：只做趋势提醒，
#       不基于单次记录诊断营养不良或发育异常）；
#       ENGINEERING_DESIGN §13.2；TASK_BACKLOG APC-T023。
# 设计：GrowthRuleModule 实现 RuleModule Protocol（domain="growth"）。
#       规则包 YAML 定义 WHO 百分位参考表（P0 简化 fixture：关键月龄的百分位锚点，
#       接口兼容完整 WHO LMS 表）。evaluate 输入 baby_age_days + sex + measure + value +
#       history（近 30 天），输出 percentile + z_score + trend + evidence。
# 边界：只做趋势提醒（架构 §10.2），不诊断营养不良/发育异常（PRD §11.13 限制）。
#       趋势不得单点强告警（与 thresholds 域一致，PRD §12.3）。

"""生长规则域（APC-T023）。

``GrowthRuleModule`` 实现 ``RuleModule`` Protocol（``domain="growth"``）。

规则包 YAML（``config/rules/growth/who-0-5.yaml``）定义 WHO 0–5 岁百分位参考表
（P0 简化 fixture：关键月龄的 P3/P15/P50/P85/P97 锚点，按性别 + measure 分条；
接口兼容完整 WHO LMS 表——V1 可替换为 LMS 参数精确计算）。``evaluate`` 输入
``baby_age_days`` + ``variables.sex`` + ``variables.measure``（weight_kg/length_cm/
head_circumference_cm）+ ``variables.value`` + ``variables.history``（近 30 天记录），
输出 ``percentile`` + ``z_score`` + ``trend`` + ``evidence``。

计算：
    1. 按 sex + measure + baby_age_days 在参考表插值取 P50 与标准差代理（P50-P3 近似 1.88σ）。
    2. z_score = (value - P50) / sigma；percentile 由 z_score 经正态 CDF 近似（erf）。
    3. 趋势：history 近 30 天百分位变化 > ``trend_delta_pct`` → 趋势提醒（黄/橙），
       单点不触发（PRD §11.13 限制 + §12.3 双条件精神）。

限制（PRD §11.13）：只做趋势提醒，不基于单次记录诊断营养不良或发育异常。
输出（``outputs``）：``percentile`` + ``z_score`` + ``measure`` + ``sex`` + ``trend`` +
``alert_level`` + ``advice``。``evidence`` 含 rule_id + policy_version + 文本（§15.4）。
"""

from __future__ import annotations

import math
from typing import Any

from ..domain.models import (
    EvidenceRef,
    RuleContext,
    RuleDomain,
    RuleInput,
    RulePack,
    RuleResult,
    Verdict,
)

# 趋势提醒阈值（百分位变化幅度，PRD §11.13 百分位异常变化提醒）。
TREND_DELTA_PCT = 25  # 近 30 天百分位变化 ≥25 个百分点 → 趋势提醒。
# WHO 百分位近似：P3/P97 对应 ±1.881σ，P15/P85 对应 ±1.036σ。sigma 代理用 (P50-P3)/1.881。
_Z_P3 = 1.881
_Z_P15 = 1.036


class GrowthRuleModule:
    """生长规则模块（APC-T023，domain="growth"）。

    WHO 百分位参考表从规则包 YAML 加载（按 sex + measure 分条，每条含关键月龄锚点）。
    ``evaluate`` 按输入插值计算 percentile/z_score，叠加趋势提醒。规则包版本化（§13.2）。
    """

    domain: RuleDomain = "growth"

    def __init__(self, pack: RulePack) -> None:
        self._pack = pack
        self._rule_version = f"{pack.policy_type}@{pack.version}"
        # 参考表：{(sex, measure): {age_months: {p3, p15, p50, p85, p97}}}（百分位锚点，float | None）
        self._refs: dict[tuple[str, str], dict[int, dict[str, float | None]]] = {}
        self._trend_delta = TREND_DELTA_PCT
        for rule in pack.rules:
            sex, measure = _extract_sex_measure(rule.conditions)
            if sex is None or measure is None:
                continue
            outputs = dict(rule.action.outputs)
            age_months = _as_int(outputs.pop("age_months", None))
            if age_months is None:
                continue
            ref = {
                "p3": _as_float(outputs.get("p3")),
                "p15": _as_float(outputs.get("p15")),
                "p50": _as_float(outputs.get("p50")),
                "p85": _as_float(outputs.get("p85")),
                "p97": _as_float(outputs.get("p97")),
            }
            self._refs.setdefault((sex, measure), {})[age_months] = ref
            if "trend_delta_pct" in outputs:
                td = _as_int(outputs.get("trend_delta_pct"))
                if td is not None:
                    self._trend_delta = td

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        """计算 WHO 百分位 + 趋势提醒 → RuleResult（不诊断，只提醒）。"""
        variables = input_.variables
        sex = str(variables.get("sex", "")).lower()
        measure = str(variables.get("measure", ""))
        value = _as_float(variables.get("value"))

        # 1. 缺 sex/measure/value → info，不出百分位。
        if not sex or not measure or value is None:
            return self._result(
                "info",
                "insufficient_input",
                "缺 sex/measure/value，无法计算百分位",
                [],
            )

        key = (sex, measure)
        if key not in self._refs:
            return self._result(
                "info",
                "unknown_measure",
                f"无 {sex}/{measure} 参考表",
                [],
            )

        # 2. 按 baby_age_days 在参考表插值取 P50 与 sigma 代理。
        age_months = (input_.baby_age_days or 0) // 30
        p50, sigma = _interpolate(self._refs[key], age_months)
        if p50 is None or sigma is None or sigma <= 0:
            return self._result(
                "info",
                "out_of_range",
                f"{sex}/{measure} 在 {age_months} 月龄无参考数据",
                [],
            )

        # 3. z_score + percentile（正态 CDF 近似）。
        z_score = (value - p50) / sigma
        percentile = _normal_cdf(z_score) * 100.0

        # 4. 趋势：history 近 30 天百分位变化。
        trend, alert_level, advice = _assess_trend(
            variables.get("history"), percentile, self._trend_delta
        )

        outputs: dict[str, Any] = {
            "percentile": round(percentile, 1),
            "z_score": round(z_score, 2),
            "measure": measure,
            "sex": sex,
            "trend": trend,
            "alert_level": alert_level,
            "advice": advice,
        }
        evidence_text = (
            f"WHO 百分位 {sex}/{measure}：P{percentile:.1f}（z={z_score:.2f}），"
            f"趋势={trend}（PRD §11.13，只提醒不诊断）"
        )
        return self._result(
            _verdict_for(alert_level),
            "growth_assessed",
            evidence_text,
            [EvidenceRef(rule_id="growth", policy_version=ctx.policy_version, text=evidence_text)],
            outputs=outputs,
        )

    def _result(
        self,
        verdict: Verdict,
        reason_code: str,
        message: str,
        evidence: list[EvidenceRef],
        outputs: dict[str, Any] | None = None,
    ) -> RuleResult:
        return RuleResult(
            verdict=verdict,
            outputs=outputs or {},
            evidence=evidence,
            rule_version=self._rule_version,
            reason_code=reason_code,
        )


# ---- 辅助 ----


def _extract_sex_measure(conditions: list) -> tuple[str | None, str | None]:
    """从 rule.conditions 取 variables.sex 与 variables.measure 的 eq 匹配值。"""
    sex: str | None = None
    measure: str | None = None
    for cond in conditions:
        if cond.op == "eq":
            if cond.field == "variables.sex":
                sex = str(cond.value)
            elif cond.field == "variables.measure":
                measure = str(cond.value)
    return sex, measure


def _interpolate(
    refs: dict[int, dict[str, float | None]], age_months: int
) -> tuple[float | None, float | None]:
    """按 age_months 在参考表锚点间线性插值取 (P50, sigma)。

    sigma 代理 = (P50 - P3) / 1.881（P3 对应 -1.881σ）。超出锚点范围用最近锚点。
    """
    if not refs:
        return None, None
    months = sorted(refs.keys())
    if age_months <= months[0]:
        ref = refs[months[0]]
    elif age_months >= months[-1]:
        ref = refs[months[-1]]
    else:
        # 找包围 age_months 的两个锚点。
        lo = months[0]
        hi = months[-1]
        for i in range(len(months) - 1):
            if months[i] <= age_months <= months[i + 1]:
                lo, hi = months[i], months[i + 1]
                break
        ref_lo, ref_hi = refs[lo], refs[hi]
        if hi == lo:
            ref = ref_lo
        else:
            lo_p50, hi_p50 = ref_lo["p50"], ref_hi["p50"]
            lo_p3, hi_p3 = ref_lo["p3"], ref_hi["p3"]
            if lo_p50 is None or hi_p50 is None or lo_p3 is None or hi_p3 is None:
                return None, None
            t = (age_months - lo) / (hi - lo)
            p50 = lo_p50 + t * (hi_p50 - lo_p50)
            p3 = lo_p3 + t * (hi_p3 - lo_p3)
            sigma = (p50 - p3) / _Z_P3 if (p50 - p3) > 0 else None
            return p50, sigma
    p50_val: float | None = ref.get("p50")
    p3_val: float | None = ref.get("p3")
    if p50_val is None or p3_val is None:
        return None, None
    sigma = (p50_val - p3_val) / _Z_P3 if (p50_val - p3_val) > 0 else None
    return p50_val, sigma


def _normal_cdf(z: float) -> float:
    """正态分布 CDF 近似（erf），用于 z_score → percentile。"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _assess_trend(
    history: Any, current_percentile: float, trend_delta: int
) -> tuple[str, str, str]:
    """评估近 30 天百分位趋势 → (trend, alert_level, advice)。

    history 支持 list[dict]（``[{"age_days": 30, "percentile": 50}, ...]``）或
    list[float]（百分位序列）。取最早与当前对比，变化幅度 ≥ trend_delta → 趋势提醒。
    单点或 history 不足 → 无趋势（PRD §11.13 限制 + §12.3 精神）。
    """
    if history is None:
        return "stable", "info", "继续观察生长曲线"
    pcts = _extract_percentiles(history)
    if len(pcts) < 1:
        return "stable", "info", "继续观察生长曲线"

    # 趋势 = current - earliest(history)：至少 1 个历史点即可比较
    # （current 是当前点，history 提供对比基线；PRD §11.13 近 30 天趋势）。
    earliest = pcts[0]
    delta = current_percentile - earliest
    if abs(delta) >= trend_delta:
        if delta < 0:
            return "declining", "yellow", "百分位下降趋势，建议咨询医生关注生长"
        return "rising", "yellow", "百分位上升趋势，建议咨询医生关注生长"
    return "stable", "info", "生长曲线平稳"


def _extract_percentiles(history: Any) -> list[float]:
    """从 history 提取百分位序列（升序按 age_days）。"""
    if isinstance(history, list):
        if not history:
            return []
        if isinstance(history[0], dict):
            items = [
                (d.get("age_days", 0), _as_float(d.get("percentile")))
                for d in history
                if isinstance(d, dict) and d.get("percentile") is not None
            ]
            items.sort(key=lambda x: x[0])
            return [p for _, p in items if p is not None]
        # list[float]：百分位序列。
        result: list[float] = []
        for p in history:
            fp = _as_float(p)
            if fp is not None:
                result.append(fp)
        return result
    return []


def _verdict_for(level: str) -> Verdict:
    if level in ("orange", "yellow"):
        return "warn"
    return "info"


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


__all__ = ["TREND_DELTA_PCT", "GrowthRuleModule"]
