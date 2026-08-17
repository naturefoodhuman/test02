# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""ThresholdRuleModule 单元测试（APC-T021）。

用测试专用 RulePack 验证趋势双条件各分支：双条件命中/单点不触发/偏离不足/
mmWave 约束/未知 metric。不依赖 DB（纯内存求值）。asyncio_mode=auto。
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
from server.app.rule_engine.domains.thresholds import ThresholdRuleModule

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


def _pack() -> RulePack:
    """测试专用阈值规则包（feeding orange / diaper yellow）。"""
    return RulePack(
        policy_type="thresholds",
        region="CN",
        version=1,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id="feeding_drop_trend",
                conditions=[
                    RuleCondition(op="eq", field="variables.metric", value="feeding_amount")
                ],
                action=RuleAction(
                    verdict="warn",
                    outputs={"min_days": 2, "deviation_pct": 20.0, "alert_level": "orange"},
                    reason_code="feeding_drop_trend",
                    evidence_text="奶量下降橙色",
                ),
            ),
            Rule(
                rule_id="wet_diaper_drop_trend",
                conditions=[
                    RuleCondition(op="eq", field="variables.metric", value="wet_diaper_count")
                ],
                action=RuleAction(
                    verdict="warn",
                    outputs={"min_days": 2, "deviation_pct": 30.0, "alert_level": "yellow"},
                    reason_code="wet_diaper_drop_trend",
                    evidence_text="湿尿布减少黄色",
                ),
            ),
        ],
    )


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


async def test_threshold_double_condition_met_orange():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 3, "deviation_pct": -25.0}
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "orange"
    assert r.outputs["metric"] == "feeding_amount"
    assert r.outputs["consecutive_days"] == 3
    assert r.reason_code == "trend_alert"


async def test_threshold_single_day_not_triggered():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 1, "deviation_pct": -50.0}
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "trend_not_met"


async def test_threshold_deviation_not_enough():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 2, "deviation_pct": -15.0}
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "trend_not_met"


async def test_threshold_positive_deviation_counts():
    """偏离幅度取 abs，正偏离也触发（如奶量异常增加）。"""
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 2, "deviation_pct": 25.0}
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "orange"


async def test_threshold_wet_diaper_yellow():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            variables={"metric": "wet_diaper_count", "consecutive_days": 2, "deviation_pct": -35.0}
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "yellow"


async def test_threshold_unknown_metric_info():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(variables={"metric": "heart_rate", "consecutive_days": 5, "deviation_pct": 80.0}),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "unknown_metric"


async def test_threshold_missing_metric_info():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(variables={"consecutive_days": 5, "deviation_pct": 80.0}), _ctx()
    )
    assert r.verdict == "info"
    assert r.reason_code == "unknown_metric"


async def test_threshold_mmwave_caps_red_to_orange():
    """规则包配 red 但 signal_source=mmwave → 降级 orange（§13.2）。"""
    pack = RulePack(
        policy_type="thresholds",
        region="CN",
        version=1,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id="red_metric",
                conditions=[
                    RuleCondition(op="eq", field="variables.metric", value="critical_metric")
                ],
                action=RuleAction(
                    verdict="block",
                    outputs={"min_days": 1, "deviation_pct": 50.0, "alert_level": "red"},
                    reason_code="red_metric",
                    evidence_text="critical",
                ),
            ),
        ],
    )
    m = ThresholdRuleModule(pack)
    r = await m.evaluate(
        RuleInput(
            variables={
                "metric": "critical_metric",
                "consecutive_days": 2,
                "deviation_pct": 60.0,
                "signal_source": "mmwave",
            }
        ),
        _ctx(),
    )
    assert r.outputs["alert_level"] == "orange"
    assert r.verdict == "warn"


async def test_threshold_evidence_carries_policy_version():
    m = ThresholdRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 2, "deviation_pct": -25.0}
        ),
        _ctx(),
    )
    assert r.evidence[0].policy_version == 1
    assert r.evidence[0].rule_id == "thresholds"
