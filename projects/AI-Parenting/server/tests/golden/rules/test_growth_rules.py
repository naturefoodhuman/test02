# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""生长规则包黄金用例（APC-T023）。

加载 ``config/rules/growth/who-0-5.yaml``，经 ``GrowthRuleModule`` 求值，验证
男/女、不同月龄、边界百分位（PRD §11.13）。golden 用例固定输入断言 ``RuleResult``。
asyncio_mode=auto。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleInput
from server.app.rule_engine.domains.growth import GrowthRuleModule
from server.app.rule_engine.loader import load_pack

pytestmark = pytest.mark.golden

RULES_DIR = Path(__file__).resolve().parents[4] / "config" / "rules"
GROWTH_PACK = RULES_DIR / "growth" / "who-0-5.yaml"

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def growth_module() -> GrowthRuleModule:
    pack = load_pack(GROWTH_PACK)
    return GrowthRuleModule(pack)


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


async def test_golden_growth_male_weight_p50(growth_module: GrowthRuleModule):
    """男 0 月体重 3.3kg（P50）→ percentile≈50，趋势 stable。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"sex": "male", "measure": "weight_kg", "value": 3.3},
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "growth_assessed"
    assert r.rule_version == "growth@1"
    assert 45 <= r.outputs["percentile"] <= 55
    assert r.outputs["trend"] == "stable"
    assert r.outputs["measure"] == "weight_kg"
    assert r.outputs["sex"] == "male"
    assert len(r.evidence) == 1


async def test_golden_growth_female_weight_p50(growth_module: GrowthRuleModule):
    """女 0 月体重 3.2kg（P50）→ percentile≈50。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"sex": "female", "measure": "weight_kg", "value": 3.2},
        ),
        _ctx(),
    )
    assert 45 <= r.outputs["percentile"] <= 55


async def test_golden_growth_male_6m_interpolated(growth_module: GrowthRuleModule):
    """男 6 月（180 天）体重 7.9kg（P50）→ percentile≈50（命中锚点）。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=180,
            variables={"sex": "male", "measure": "weight_kg", "value": 7.9},
        ),
        _ctx(),
    )
    assert 45 <= r.outputs["percentile"] <= 55


async def test_golden_growth_male_3m_interpolated(growth_module: GrowthRuleModule):
    """男 3 月（90 天）体重在 0-6 月锚点间插值 → 合理百分位。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=90,
            variables={"sex": "male", "measure": "weight_kg", "value": 6.0},
        ),
        _ctx(),
    )
    assert 0 <= r.outputs["percentile"] <= 100
    assert r.outputs["z_score"] is not None


async def test_golden_growth_high_percentile(growth_module: GrowthRuleModule):
    """男 0 月体重 4.0kg（P97）→ 高百分位（≥90）。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"sex": "male", "measure": "weight_kg", "value": 4.0},
        ),
        _ctx(),
    )
    assert r.outputs["percentile"] >= 90


async def test_golden_growth_low_percentile(growth_module: GrowthRuleModule):
    """男 0 月体重 2.5kg（P3）→ 低百分位（≤10）。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"sex": "male", "measure": "weight_kg", "value": 2.5},
        ),
        _ctx(),
    )
    assert r.outputs["percentile"] <= 10


async def test_golden_growth_trend_rising(growth_module: GrowthRuleModule):
    """近 30 天百分位上升 ≥25 → rising 黄色提醒（PRD §11.13 百分位异常变化提醒）。

    current percentile≈50（P50），earliest=15 → delta=+35 ≥ 25 → rising。
    """
    r = await growth_module.evaluate(
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


async def test_golden_growth_trend_declining(growth_module: GrowthRuleModule):
    """近 30 天百分位下降 ≥25 → declining 黄色提醒。

    current percentile≈3（P3 体重 2.5kg），earliest=60 → delta=-57 ≤ -25 → declining。
    """
    r = await growth_module.evaluate(
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
    assert r.verdict == "warn"


async def test_golden_growth_trend_stable(growth_module: GrowthRuleModule):
    """近 30 天百分位变化 < 25 → stable，无提醒。"""
    r = await growth_module.evaluate(
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


async def test_golden_growth_missing_value_info(growth_module: GrowthRuleModule):
    """缺 value → info insufficient_input，不出百分位。"""
    r = await growth_module.evaluate(
        RuleInput(baby_age_days=0, variables={"sex": "male", "measure": "weight_kg"}),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "insufficient_input"


async def test_golden_growth_unknown_measure_info(growth_module: GrowthRuleModule):
    """未知 measure → info unknown_measure。"""
    r = await growth_module.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"sex": "male", "measure": "bmi", "value": 16.0},
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "unknown_measure"
