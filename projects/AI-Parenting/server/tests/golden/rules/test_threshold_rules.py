# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""告警阈值规则包黄金用例（APC-T021）。

加载 ``config/rules/thresholds/base-1.yaml``，经 ``ThresholdRuleModule`` 求值，验证趋势双条件：
连续 N 天 + 偏离 X% 同时满足才触发；单点异常不触发；mmWave 单信号最多橙色。
asyncio_mode=auto。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleInput
from server.app.rule_engine.domains.thresholds import ThresholdRuleModule
from server.app.rule_engine.loader import load_pack

pytestmark = pytest.mark.golden

RULES_DIR = Path(__file__).resolve().parents[4] / "config" / "rules"
THRESHOLDS_PACK = RULES_DIR / "thresholds" / "base-1.yaml"

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def thresholds_module() -> ThresholdRuleModule:
    pack = load_pack(THRESHOLDS_PACK)
    return ThresholdRuleModule(pack)


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


async def test_golden_threshold_feeding_drop_trend_orange(thresholds_module: ThresholdRuleModule):
    """奶量连续 2 天偏离 25% → orange warn（双条件满足）。"""
    r = await thresholds_module.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 2, "deviation_pct": -25.0}
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "orange"
    assert r.outputs["metric"] == "feeding_amount"
    assert r.reason_code == "trend_alert"
    assert r.rule_version == "thresholds@1"


async def test_golden_threshold_single_day_not_triggered(thresholds_module: ThresholdRuleModule):
    """单点异常（consecutive_days=1）→ info，不触发（PRD §12.3）。"""
    r = await thresholds_module.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 1, "deviation_pct": -30.0}
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "trend_not_met"


async def test_golden_threshold_deviation_not_enough(thresholds_module: ThresholdRuleModule):
    """偏离不足（连续 2 天但偏离 10% < 20%）→ info，不触发。"""
    r = await thresholds_module.evaluate(
        RuleInput(
            variables={"metric": "feeding_amount", "consecutive_days": 2, "deviation_pct": -10.0}
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "trend_not_met"


async def test_golden_threshold_wet_diaper_yellow(thresholds_module: ThresholdRuleModule):
    """湿尿布连续 2 天偏离 35% → yellow warn。"""
    r = await thresholds_module.evaluate(
        RuleInput(
            variables={"metric": "wet_diaper_count", "consecutive_days": 2, "deviation_pct": -35.0}
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs["alert_level"] == "yellow"


async def test_golden_threshold_unknown_metric_info(thresholds_module: ThresholdRuleModule):
    """未知 metric → info unknown_metric。"""
    r = await thresholds_module.evaluate(
        RuleInput(
            variables={"metric": "unknown_metric", "consecutive_days": 5, "deviation_pct": 50.0}
        ),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "unknown_metric"
