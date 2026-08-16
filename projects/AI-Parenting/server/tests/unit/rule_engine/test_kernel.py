# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""Rule Engine 求值核心单元测试（APC-T018）。

覆盖算子语义、字段路径解析、match_rule（AND）、evaluate_pack（首个匹配/默认 info）。
不依赖 DB（纯函数求值）。asyncio_mode=auto，测试用 async 函数。
"""

from __future__ import annotations

from datetime import UTC, datetime

from server.app.rule_engine.domain.models import (
    Rule,
    RuleAction,
    RuleCondition,
    RuleContext,
    RuleInput,
    RulePack,
)
from server.app.rule_engine.kernel import _compare, _resolve_field, evaluate_pack, match_rule

NOW = datetime(2026, 8, 16, 0, 0, 0, tzinfo=UTC)


def _pack(rules: list[Rule], *, policy_type: str = "triage", version: int = 1) -> RulePack:
    return RulePack(
        policy_type=policy_type,
        region="CN",
        version=version,
        effective_from=NOW,
        source="test",
        rule_text="test",
        display_text="test",
        rules=rules,
    )


def _rule(
    rule_id: str,
    conditions: list[RuleCondition],
    *,
    verdict: str = "warn",
    reason_code: str = "rc",
    outputs: dict | None = None,
) -> Rule:
    return Rule(
        rule_id=rule_id,
        conditions=conditions,
        action=RuleAction(
            verdict=verdict,  # type: ignore[arg-type]
            outputs=outputs or {},
            reason_code=reason_code,
            evidence_text="e",
        ),
    )


# ---- 算子语义 ----


def test_compare_eq_ne():
    assert _compare("eq", 1, 1) is True
    assert _compare("eq", 1, 2) is False
    assert _compare("ne", 1, 2) is True
    assert _compare("ne", None, 1) is True  # ne 对 None 成立


def test_compare_lt_lte_gt_gte_none_conservative():
    # actual/expected 为 None 时除 ne/not_in 外一律 False（保守）。
    assert _compare("lt", None, 1) is False
    assert _compare("lt", 1, None) is False
    assert _compare("lt", 1, 2) is True
    assert _compare("lte", 2, 2) is True
    assert _compare("gt", 2, 1) is True
    assert _compare("gte", 2, 2) is True
    # 非数值保守 False。
    assert _compare("gt", "a", 1) is False


def test_compare_in_not_in():
    assert _compare("in", "wet", ["wet", "dirty"]) is True
    assert _compare("in", "x", ["wet"]) is False
    assert _compare("in", None, ["wet"]) is False  # None 不 in
    assert _compare("not_in", "x", ["wet"]) is True
    assert _compare("not_in", None, ["wet"]) is True  # None not_in 成立（保守放行）


def test_compare_range_closed_interval():
    assert _compare("range", 38.5, [38.0, 39.0]) is True
    assert _compare("range", 38.0, [38.0, 39.0]) is True  # 闭区间含端点
    assert _compare("range", 39.0, [38.0, 39.0]) is True
    assert _compare("range", 37.9, [38.0, 39.0]) is False
    assert _compare("range", None, [38.0, 39.0]) is False
    assert _compare("range", 38.5, [38.0]) is False  # 长度不符


def test_compare_unknown_op_returns_false():
    assert _compare("weird", 1, 1) is False


# ---- 字段路径解析 ----


def test_resolve_field_top_level():
    inp = RuleInput(baby_age_days=120)
    assert _resolve_field(inp, "baby_age_days") == 120


def test_resolve_field_variables_nested():
    inp = RuleInput(variables={"temperature_c": 38.5, "nested": {"x": 1}})
    assert _resolve_field(inp, "variables.temperature_c") == 38.5
    assert _resolve_field(inp, "variables.nested.x") == 1


def test_resolve_field_variables_missing_returns_none():
    inp = RuleInput(variables={"a": 1})
    assert _resolve_field(inp, "variables.missing") is None
    assert _resolve_field(inp, "variables.a.b") is None  # 非 dict 中途


def test_resolve_field_unknown_top_level_returns_none():
    inp = RuleInput()
    assert _resolve_field(inp, "nonexistent") is None


# ---- match_rule（AND）----


def test_match_rule_all_conditions_required():
    rule = _rule(
        "r1",
        [
            RuleCondition(op="lt", field="baby_age_days", value=90),
            RuleCondition(op="gte", field="variables.temperature_c", value=38.0),
        ],
    )
    # 两个条件都满足 → 匹配。
    assert match_rule(rule, RuleInput(baby_age_days=30, variables={"temperature_c": 38.5})) is True
    # 缺一个 → 不匹配。
    assert match_rule(rule, RuleInput(baby_age_days=30, variables={"temperature_c": 37.0})) is False
    assert (
        match_rule(rule, RuleInput(baby_age_days=120, variables={"temperature_c": 38.5})) is False
    )


def test_match_rule_no_conditions_matches():
    # 无条件规则恒匹配（默认动作）。
    rule = _rule("r0", [])
    assert match_rule(rule, RuleInput()) is True


# ---- evaluate_pack ----


def test_evaluate_pack_first_match_wins():
    pack = _pack(
        [
            _rule(
                "red", [RuleCondition(op="lt", field="baby_age_days", value=90)], verdict="block"
            ),
            _rule(
                "orange", [RuleCondition(op="gte", field="baby_age_days", value=90)], verdict="warn"
            ),
        ]
    )
    ctx = RuleContext(policy_version=1)
    r = evaluate_pack(pack, RuleInput(baby_age_days=30, variables={"temperature_c": 38.5}), ctx)
    assert r.verdict == "block"
    assert r.reason_code == "rc"
    assert r.rule_version == "triage@1"
    assert len(r.evidence) == 1
    assert r.evidence[0].rule_id == "red"
    assert r.evidence[0].policy_version == 1


def test_evaluate_pack_no_match_returns_info():
    pack = _pack([_rule("red", [RuleCondition(op="lt", field="baby_age_days", value=90)])])
    ctx = RuleContext(policy_version=1)
    r = evaluate_pack(pack, RuleInput(baby_age_days=120), ctx)
    assert r.verdict == "info"
    assert r.reason_code == "no_match"
    assert r.outputs == {}
    assert r.evidence == []
    assert r.rule_version == "triage@1"


def test_evaluate_pack_outputs_copied_not_shared():
    rule = _rule(
        "r1",
        [RuleCondition(op="eq", field="baby_age_days", value=1)],
        outputs={"alert_level": "red"},
    )
    pack = _pack([rule])
    ctx = RuleContext(policy_version=2)
    r1 = evaluate_pack(pack, RuleInput(baby_age_days=1), ctx)
    r2 = evaluate_pack(pack, RuleInput(baby_age_days=1), ctx)
    r1.outputs["x"] = 1
    assert "x" not in r2.outputs  # 各结果 outputs 独立拷贝。
