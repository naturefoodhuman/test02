# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""分诊规则包黄金用例（APC-T021）。

加载 ``config/rules/triage/base-1.yaml``，经 ``TriageRuleModule`` 求值，验证生产行为：
体温阈值（红/橙/黄）+ 危险信号升级 + mmWave 单信号约束 + 就医建议。
golden 用例固定输入断言 ``RuleResult``（架构 §14：Rule Engine 必须先有 golden 用例）。
asyncio_mode=auto。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleInput
from server.app.rule_engine.domains.triage import TriageRuleModule
from server.app.rule_engine.loader import load_pack

pytestmark = pytest.mark.golden

RULES_DIR = Path(__file__).resolve().parents[4] / "config" / "rules"
TRIAGE_PACK = RULES_DIR / "triage" / "base-1.yaml"

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def triage_module() -> TriageRuleModule:
    pack = load_pack(TRIAGE_PACK)
    return TriageRuleModule(pack)


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


async def test_golden_triage_fever_under_3mo_red(triage_module: TriageRuleModule):
    """3 月龄以下 ≥38°C → red block（强红线，PRD §11.9）。"""
    r = await triage_module.evaluate(
        RuleInput(baby_age_days=30, variables={"temperature_c": 38.5}), _ctx()
    )
    assert r.verdict == "block"
    assert r.outputs["alert_level"] == "red"
    assert r.reason_code == "fever_under_3mo_red"
    assert r.rule_version == "triage@1"
    assert "立即就医" in r.outputs["advice"]
    assert len(r.evidence) == 1


async def test_golden_triage_fever_over_3mo_orange(triage_module: TriageRuleModule):
    """3 月龄以上 ≥39°C → orange warn。"""
    r = await triage_module.evaluate(
        RuleInput(baby_age_days=120, variables={"temperature_c": 39.5}), _ctx()
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "orange"
    assert r.reason_code == "fever_over_3mo_orange"


async def test_golden_triage_fever_over_3mo_yellow(triage_module: TriageRuleModule):
    """3 月龄以上 38~39°C → yellow warn。"""
    r = await triage_module.evaluate(
        RuleInput(baby_age_days=120, variables={"temperature_c": 38.5}), _ctx()
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "yellow"
    assert r.reason_code == "fever_over_3mo_yellow"


async def test_golden_triage_normal_temp_info(triage_module: TriageRuleModule):
    """正常体温 → info（无 alert_level 升级）。"""
    r = await triage_module.evaluate(
        RuleInput(baby_age_days=120, variables={"temperature_c": 37.2}), _ctx()
    )
    assert r.verdict == "info"
    assert r.outputs["alert_level"] == "info"
    assert r.reason_code == "no_match"


async def test_golden_triage_danger_signal_upgrades_red(triage_module: TriageRuleModule):
    """危险信号命中 → 升级 red（即使体温正常）。"""
    r = await triage_module.evaluate(
        RuleInput(
            baby_age_days=120,
            variables={"temperature_c": 37.0, "danger_signals": ["convulsion"]},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.outputs["alert_level"] == "red"
    assert r.reason_code == "danger_signal_red"
    assert r.outputs["danger_signals"] == ["convulsion"]


async def test_golden_triage_mmwave_signal_capped(triage_module: TriageRuleModule):
    """mmWave 单信号触发 red → 降级 orange（§13.2 不单独触发红色医疗告警）。"""
    r = await triage_module.evaluate(
        RuleInput(
            baby_age_days=30,
            variables={"temperature_c": 38.5, "signal_source": "mmwave"},
        ),
        _ctx(),
    )
    assert r.outputs["alert_level"] == "orange"
    assert r.reason_code == "mmwave_signal_capped"
    assert r.verdict == "warn"
