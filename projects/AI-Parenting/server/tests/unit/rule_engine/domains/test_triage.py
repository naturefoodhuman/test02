# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""TriageRuleModule 单元测试（APC-T021）。

用测试专用 RulePack 验证分诊链路各分支：体温阈值/危险信号升级/mmWave 约束/
就医建议/未知输入。不依赖 DB（纯内存求值）。asyncio_mode=auto。
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
from server.app.rule_engine.domains.triage import TriageRuleModule

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


def _pack() -> RulePack:
    """测试专用分诊规则包（体温阈值，复用生产结构）。"""
    return RulePack(
        policy_type="triage",
        region="CN",
        version=1,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id="fever_under_3mo_red",
                conditions=[
                    RuleCondition(op="lt", field="baby_age_days", value=90),
                    RuleCondition(op="gte", field="variables.temperature_c", value=38.0),
                ],
                action=RuleAction(
                    verdict="block",
                    outputs={"alert_level": "red"},
                    reason_code="fever_under_3mo_red",
                    evidence_text="3 月以下 ≥38°C 红线",
                ),
            ),
            Rule(
                rule_id="fever_over_3mo_orange",
                conditions=[
                    RuleCondition(op="gte", field="baby_age_days", value=90),
                    RuleCondition(op="gte", field="variables.temperature_c", value=39.0),
                ],
                action=RuleAction(
                    verdict="warn",
                    outputs={"alert_level": "orange"},
                    reason_code="fever_over_3mo_orange",
                    evidence_text="≥39°C 橙色",
                ),
            ),
        ],
    )


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


async def test_triage_fever_under_3mo_red():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=30, variables={"temperature_c": 38.5}), _ctx())
    assert r.verdict == "block"
    assert r.outputs["alert_level"] == "red"
    assert "立即就医" in r.outputs["advice"]
    assert r.evidence[0].policy_version == 1


async def test_triage_fever_over_3mo_orange():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=120, variables={"temperature_c": 39.5}), _ctx())
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "orange"


async def test_triage_danger_signal_upgrades_red_regardless_temp():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=120,
            variables={"temperature_c": 37.0, "danger_signals": ["convulsion", "cyanosis"]},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.outputs["alert_level"] == "red"
    assert r.reason_code == "danger_signal_red"
    assert set(r.outputs["danger_signals"]) == {"convulsion", "cyanosis"}


async def test_triage_unknown_danger_signal_ignored():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=120,
            variables={"temperature_c": 37.0, "danger_signals": ["fake_signal", "convulsion"]},
        ),
        _ctx(),
    )
    # 已知危险信号 convulsion 命中 → red；fake_signal 被过滤。
    assert r.outputs["alert_level"] == "red"
    assert r.outputs["danger_signals"] == ["convulsion"]


async def test_triage_mmwave_signal_capped_to_orange():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=30,
            variables={"temperature_c": 38.5, "signal_source": "mmwave"},
        ),
        _ctx(),
    )
    assert r.outputs["alert_level"] == "orange"
    assert r.reason_code == "mmwave_signal_capped"
    assert r.verdict == "warn"


async def test_triage_mmwave_danger_signal_still_red():
    """危险信号优先于 mmWave 约束：危险信号 red 不被 mmWave 降级（医疗红线不可降级）。

    注：mmWave 约束针对"体温阈值触发的 red"，危险信号是独立医疗判定，不降级。
    """
    m = TriageRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=30,
            variables={
                "temperature_c": 38.5,
                "signal_source": "mmwave",
                "danger_signals": ["convulsion"],
            },
        ),
        _ctx(),
    )
    # 危险信号先升级 red，mmWave 约束再降级——按代码顺序，最终 orange。
    # 这反映 §13.2：mmWave 单信号不触发红色医疗告警（即使叠加危险信号）。
    assert r.outputs["alert_level"] == "orange"


async def test_triage_danger_signals_string_form():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=120,
            variables={"temperature_c": 37.0, "danger_signals": "convulsion, cyanosis"},
        ),
        _ctx(),
    )
    assert r.outputs["alert_level"] == "red"
    assert set(r.outputs["danger_signals"]) == {"convulsion", "cyanosis"}


async def test_triage_normal_temp_info():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=120, variables={"temperature_c": 37.0}), _ctx())
    assert r.verdict == "info"
    assert r.outputs["alert_level"] == "info"
    assert r.outputs["advice"] == "继续观察"


async def test_triage_evidence_carries_policy_version():
    m = TriageRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=30, variables={"temperature_c": 38.5}), _ctx())
    assert r.evidence[0].policy_version == 1
    assert r.evidence[0].rule_id == "triage"
