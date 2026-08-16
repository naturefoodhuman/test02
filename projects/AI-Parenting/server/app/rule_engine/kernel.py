# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/rule_engine/kernel.py —— Rule Engine 求值核心（APC-T018）。
# 依据：ENGINEERING_DESIGN §5.3、§13.2；TASK_BACKLOG APC-T018（需新算子则扩展 kernel）。
# 设计：纯函数求值——按 Rule.conditions 匹配（AND），匹配则产出 RuleAction。
#       算子：eq/ne/lt/lte/gt/gte/in/not_in/range。字段路径支持 "variables.xxx" 嵌套。
#       evaluate_pack：按规则包顺序求值，首个匹配规则产出（或默认 info）。
# 边界：只做条件匹配 + 动作产出，不做医疗判断（医疗规则在规则域 YAML）。

"""Rule Engine 求值核心（APC-T018）。

纯函数求值：按 ``Rule.conditions`` 匹配（全部满足 AND），匹配则产出 ``RuleAction``。
算子：eq/ne/lt/lte/gt/gte/in/not_in/range。字段路径支持 ``variables.xxx`` 嵌套取值。

``evaluate_pack``：按规则包顺序求值，首个匹配规则产出；无匹配返回默认 info 结果。
扩展新算子在本模块加（§13.2 "需新算子则扩展 kernel"）。
"""

from __future__ import annotations

from typing import Any

from .domain.models import (
    EvidenceRef,
    Rule,
    RuleContext,
    RuleInput,
    RulePack,
    RuleResult,
)


def _resolve_field(input_: RuleInput, field: str) -> Any:
    """按字段路径取值，支持 "variables.xxx" 嵌套与顶层字段。"""
    if field.startswith("variables."):
        keys = field.split(".")
        val: Any = input_.variables
        for k in keys[1:]:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None
        return val
    return getattr(input_, field, None)


def _compare(op: str, actual: Any, expected: Any) -> bool:
    """执行比较算子。actual/expected 为 None 时除 ne/not_in 外一律 False（保守）。"""
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op in ("lt", "lte", "gt", "gte"):
        if actual is None or expected is None:
            return False
        try:
            a = float(actual)
            e = float(expected)
        except (TypeError, ValueError):
            return False
        if op == "lt":
            return a < e
        if op == "lte":
            return a <= e
        if op == "gt":
            return a > e
        return a >= e
    if op == "in":
        if actual is None:
            return False
        return actual in expected
    if op == "not_in":
        if actual is None:
            return True  # None 不在集合内 → not_in 成立（保守放行）。
        return actual not in expected
    if op == "range":
        # expected = [lo, hi]，闭区间。
        if actual is None or not isinstance(expected, (list, tuple)) or len(expected) != 2:
            return False
        try:
            a = float(actual)
            lo = float(expected[0])
            hi = float(expected[1])
        except (TypeError, ValueError):
            return False
        return lo <= a <= hi
    return False


def match_rule(rule: Rule, input_: RuleInput) -> bool:
    """判断规则所有 conditions 是否全部满足（AND）。"""
    return all(
        _compare(cond.op, _resolve_field(input_, cond.field), cond.value)
        for cond in rule.conditions
    )


def evaluate_pack(
    pack: RulePack, input_: RuleInput, ctx: RuleContext
) -> RuleResult:
    """求值规则包：首个匹配规则产出；无匹配返回默认 info。

    ``rule_version``：``<policy_type>@<version>``。
    匹配规则的 evidence 含 rule_id + policy_version + evidence_text。
    """
    rule_version = f"{pack.policy_type}@{pack.version}"
    for rule in pack.rules:
        if match_rule(rule, input_):
            return RuleResult(
                verdict=rule.action.verdict,
                outputs=dict(rule.action.outputs),
                evidence=[
                    EvidenceRef(
                        rule_id=rule.rule_id,
                        policy_version=ctx.policy_version,
                        text=rule.action.evidence_text,
                    )
                ],
                rule_version=rule_version,
                reason_code=rule.action.reason_code,
            )
    # 无匹配：默认 info（不阻断，交由调用方决定）。
    return RuleResult(
        verdict="info",
        outputs={},
        evidence=[],
        rule_version=rule_version,
        reason_code="no_match",
    )


__all__ = ["evaluate_pack", "match_rule"]
