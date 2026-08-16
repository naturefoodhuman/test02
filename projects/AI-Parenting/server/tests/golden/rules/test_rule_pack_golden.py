# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""规则包黄金用例（APC-T018）。

加载 ``config/rules/triage/base-1.yaml`` 示例规则包，固定输入断言 ``RuleResult``
（verdict/outputs/evidence/rule_version/reason_code）。golden 用例先于业务接入
（架构 §14：Rule Engine 必须先有 golden 用例才可接入）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleInput
from server.app.rule_engine.kernel import evaluate_pack
from server.app.rule_engine.loader import load_pack

pytestmark = pytest.mark.golden

RULES_DIR = Path(__file__).resolve().parents[4] / "config" / "rules"
TRIAGE_PACK = RULES_DIR / "triage" / "base-1.yaml"

NOW = datetime(2026, 8, 16, 0, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def triage_pack():
    return load_pack(TRIAGE_PACK)


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


def test_golden_fever_under_3mo_red(triage_pack):
    # 30 天 + 38.5°C → 强红线 block。
    r = evaluate_pack(
        triage_pack,
        RuleInput(baby_age_days=30, variables={"temperature_c": 38.5}),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.outputs == {"alert_level": "red"}
    assert r.reason_code == "fever_under_3mo_red"
    assert r.rule_version == "triage@1"
    assert len(r.evidence) == 1
    assert r.evidence[0].rule_id == "fever_under_3mo_red"
    assert r.evidence[0].policy_version == 1


def test_golden_fever_over_3mo_orange(triage_pack):
    # 120 天 + 39.5°C → 橙色 warn。
    r = evaluate_pack(
        triage_pack,
        RuleInput(baby_age_days=120, variables={"temperature_c": 39.5}),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs == {"alert_level": "orange"}
    assert r.reason_code == "fever_over_3mo_orange"


def test_golden_fever_over_3mo_yellow(triage_pack):
    # 120 天 + 38.5°C（38~39 闭区间）→ 黄色 warn。
    r = evaluate_pack(
        triage_pack,
        RuleInput(baby_age_days=120, variables={"temperature_c": 38.5}),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.outputs == {"alert_level": "yellow"}
    assert r.reason_code == "fever_over_3mo_yellow"


def test_golden_normal_temp_no_match(triage_pack):
    # 120 天 + 37.5°C → 无匹配，默认 info。
    r = evaluate_pack(
        triage_pack,
        RuleInput(baby_age_days=120, variables={"temperature_c": 37.5}),
        _ctx(),
    )
    assert r.verdict == "info"
    assert r.reason_code == "no_match"
    assert r.outputs == {}
    assert r.evidence == []


def test_golden_boundary_3mo_exactly(triage_pack):
    # 90 天（≥90 不满足 <90 的红线条件）+ 38°C → 命中 yellow（range 含 38.0）。
    r = evaluate_pack(
        triage_pack,
        RuleInput(baby_age_days=90, variables={"temperature_c": 38.0}),
        _ctx(),
    )
    assert r.reason_code == "fever_over_3mo_yellow"


def test_golden_missing_temperature_no_match(triage_pack):
    # 缺 temperature_c（None）→ gte/range 对 None 保守 False → 无匹配 info。
    r = evaluate_pack(triage_pack, RuleInput(baby_age_days=30), _ctx())
    assert r.verdict == "info"
    assert r.reason_code == "no_match"
