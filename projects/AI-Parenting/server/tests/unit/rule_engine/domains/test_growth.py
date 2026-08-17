# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""GrowthRuleModule 单元测试（APC-T023）。

用测试专用 RulePack 验证生长百分位各分支：P50/插值/缺输入/未知 measure/
趋势上升下降/历史 list[float] 形式/不诊断。不依赖 DB（纯内存求值）。asyncio_mode=auto。
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
from server.app.rule_engine.domains.growth import GrowthRuleModule

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


def _pack() -> RulePack:
    """测试专用生长规则包（male weight 0/6/12 月锚点）。"""
    return RulePack(
        policy_type="growth",
        region="CN",
        version=1,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id="male_w_0",
                conditions=[
                    RuleCondition(op="eq", field="variables.sex", value="male"),
                    RuleCondition(op="eq", field="variables.measure", value="weight_kg"),
                ],
                action=RuleAction(
                    verdict="info",
                    outputs={
                        "age_months": 0,
                        "p3": 2.5,
                        "p15": 3.0,
                        "p50": 3.3,
                        "p85": 3.7,
                        "p97": 4.0,
                    },
                    reason_code="male_w_0",
                    evidence_text="male w 0m",
                ),
            ),
            Rule(
                rule_id="male_w_6",
                conditions=[
                    RuleCondition(op="eq", field="variables.sex", value="male"),
                    RuleCondition(op="eq", field="variables.measure", value="weight_kg"),
                ],
                action=RuleAction(
                    verdict="info",
                    outputs={
                        "age_months": 6,
                        "p3": 6.4,
                        "p15": 7.1,
                        "p50": 7.9,
                        "p85": 8.7,
                        "p97": 9.5,
                    },
                    reason_code="male_w_6",
                    evidence_text="male w 6m",
                ),
            ),
        ],
    )


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


async def test_growth_p50_at_anchor():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg", "value": 3.3}),
        _ctx(),
    )
    assert r.reason_code == "growth_assessed"
    assert 45 <= r.outputs["percentile"] <= 55
    assert abs(r.outputs["z_score"]) < 0.1


async def test_growth_interpolation_between_anchors():
    """3 月（90 天）在 0-6 月锚点间插值。"""
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=90, variables={"sex": "male", "measure": "weight_kg", "value": 5.6}
        ),
        _ctx(),
    )
    assert r.reason_code == "growth_assessed"
    assert 0 <= r.outputs["percentile"] <= 100


async def test_growth_high_percentile():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg", "value": 4.0}),
        _ctx(),
    )
    assert r.outputs["percentile"] >= 90


async def test_growth_low_percentile():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg", "value": 2.5}),
        _ctx(),
    )
    assert r.outputs["percentile"] <= 10


async def test_growth_missing_sex_info():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"measure": "weight_kg", "value": 3.3}), _ctx()
    )
    assert r.verdict == "info"
    assert r.reason_code == "insufficient_input"


async def test_growth_missing_value_info():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg"}), _ctx()
    )
    assert r.reason_code == "insufficient_input"


async def test_growth_unknown_measure_info():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "bmi", "value": 16.0}),
        _ctx(),
    )
    assert r.reason_code == "unknown_measure"


async def test_growth_unknown_sex_info():
    """female 未在测试包定义 → unknown_measure（key 不存在）。"""
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0, variables={"sex": "female", "measure": "weight_kg", "value": 3.2}
        ),
        _ctx(),
    )
    assert r.reason_code == "unknown_measure"


async def test_growth_trend_rising():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={
                "sex": "male",
                "measure": "weight_kg",
                "value": 3.3,
                "history": [{"age_days": -30, "percentile": 15}],
            },
        ),
        _ctx(),
    )
    assert r.outputs["trend"] == "rising"
    assert r.outputs["alert_level"] == "yellow"
    assert r.verdict == "warn"


async def test_growth_trend_declining():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={
                "sex": "male",
                "measure": "weight_kg",
                "value": 2.5,
                "history": [{"age_days": -30, "percentile": 60}],
            },
        ),
        _ctx(),
    )
    assert r.outputs["trend"] == "declining"
    assert r.outputs["alert_level"] == "yellow"


async def test_growth_trend_stable_small_delta():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={
                "sex": "male",
                "measure": "weight_kg",
                "value": 3.3,
                "history": [{"age_days": -30, "percentile": 45}],
            },
        ),
        _ctx(),
    )
    assert r.outputs["trend"] == "stable"
    assert r.outputs["alert_level"] == "info"


async def test_growth_trend_history_float_list():
    """history 支持 list[float] 百分位序列。"""
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={
                "sex": "male",
                "measure": "weight_kg",
                "value": 3.3,
                "history": [15.0, 20.0],
            },
        ),
        _ctx(),
    )
    # earliest=15, current≈50 → delta=35 → rising。
    assert r.outputs["trend"] == "rising"


async def test_growth_trend_insufficient_history():
    """history 只有 1 个点 → 不足判断趋势 → stable。"""
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={
                "sex": "male",
                "measure": "weight_kg",
                "value": 3.3,
                "history": [{"age_days": -30, "percentile": 50}],
            },
        ),
        _ctx(),
    )
    assert r.outputs["trend"] == "stable"


async def test_growth_no_history_stable():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg", "value": 3.3}),
        _ctx(),
    )
    assert r.outputs["trend"] == "stable"
    assert r.outputs["alert_level"] == "info"


async def test_growth_evidence_carries_policy_version():
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg", "value": 3.3}),
        _ctx(),
    )
    assert r.evidence[0].policy_version == 1
    assert r.evidence[0].rule_id == "growth"


async def test_growth_not_diagnostic():
    """单次记录不诊断：即使百分位很低也只 info（无 history 趋势），不出 warn/block。"""
    m = GrowthRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg", "value": 2.5}),
        _ctx(),
    )
    # 低百分位单点 → info（不诊断营养不良，PRD §11.13 限制）。
    assert r.verdict == "info"
    assert r.outputs["alert_level"] == "info"
