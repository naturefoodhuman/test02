# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""疫苗规则包黄金用例（APC-T022）。

加载 ``config/rules/vaccine/cn-nip-2024.yaml``，经 ``VaccineRuleModule`` 求值，验证
出生后常见计划、逾期、已接种跳过（PRD §11.12）。golden 用例固定输入断言 ``RuleResult``。
asyncio_mode=auto。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleInput
from server.app.rule_engine.domains.vaccine import VaccineRuleModule
from server.app.rule_engine.loader import load_pack

pytestmark = pytest.mark.golden

RULES_DIR = Path(__file__).resolve().parents[4] / "config" / "rules"
VACCINE_PACK = RULES_DIR / "vaccine" / "cn-nip-2024.yaml"

# 固定参考时间：2026-08-17。baby 当天出生 → baby_age_days=0。
NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def vaccine_module() -> VaccineRuleModule:
    pack = load_pack(VACCINE_PACK)
    return VaccineRuleModule(pack)


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


def _todo_for(todos: list, vaccine: str, dose: int) -> dict:
    for t in todos:
        if t["vaccine"] == vaccine and t["dose"] == dose:
            return t
    raise AssertionError(f"todo not found: {vaccine}:{dose}")


async def test_golden_vaccine_newborn_due_today(vaccine_module: VaccineRuleModule):
    """新生儿（0 天）：乙肝第1剂 + 卡介苗当天到期（due，蓝色）。"""
    r = await vaccine_module.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    assert r.verdict == "info"
    assert r.reason_code == "vaccine_plan"
    assert r.rule_version == "vaccine@1"
    assert r.outputs["region"] == "CN"
    todos = r.outputs["todos"]
    hepb1 = _todo_for(todos, "hepb", 1)
    assert hepb1["status"] == "due"
    assert hepb1["alert_level"] == "blue"
    assert hepb1["days_offset"] == 0
    bcg1 = _todo_for(todos, "bcg", 1)
    assert bcg1["status"] == "due"
    assert len(r.evidence) == 1


async def test_golden_vaccine_upcoming_14d(vaccine_module: VaccineRuleModule):
    """出生 16 天：乙肝第2剂（推荐 30 天）距到期 14 天 → upcoming（可预约）。"""
    r = await vaccine_module.evaluate(RuleInput(baby_age_days=16, variables={}), _ctx())
    hepb2 = _todo_for(r.outputs["todos"], "hepb", 2)
    assert hepb2["status"] == "upcoming"
    assert hepb2["alert_level"] == "blue"
    assert hepb2["days_offset"] == 14


async def test_golden_vaccine_due_soon_3d(vaccine_module: VaccineRuleModule):
    """出生 27 天：乙肝第2剂（推荐 30 天）距到期 3 天 → due_soon（准备提醒）。"""
    r = await vaccine_module.evaluate(RuleInput(baby_age_days=27, variables={}), _ctx())
    hepb2 = _todo_for(r.outputs["todos"], "hepb", 2)
    assert hepb2["status"] == "due_soon"
    assert hepb2["days_offset"] == 3


async def test_golden_vaccine_overdue_blue(vaccine_module: VaccineRuleModule):
    """出生 33 天：乙肝第2剂（推荐 30 天）逾期 3 天 → overdue 蓝色。"""
    r = await vaccine_module.evaluate(RuleInput(baby_age_days=33, variables={}), _ctx())
    hepb2 = _todo_for(r.outputs["todos"], "hepb", 2)
    assert hepb2["status"] == "overdue"
    assert hepb2["alert_level"] == "blue"
    assert hepb2["days_offset"] == -3


async def test_golden_vaccine_overdue_yellow(vaccine_module: VaccineRuleModule):
    """出生 195 天：乙肝第3剂（推荐 180 天）逾期 15 天 → overdue 黄色。"""
    r = await vaccine_module.evaluate(RuleInput(baby_age_days=195, variables={}), _ctx())
    hepb3 = _todo_for(r.outputs["todos"], "hepb", 3)
    assert hepb3["status"] == "overdue"
    assert hepb3["alert_level"] == "yellow"
    assert hepb3["days_offset"] == -15


async def test_golden_vaccine_completed_skipped_excluded(vaccine_module: VaccineRuleModule):
    """已 completed/skipped 的剂次不出现在待办列表。"""
    r = await vaccine_module.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={
                "vaccine_records": [
                    {"vaccine": "hepb", "dose": 1, "status": "completed"},
                    {"vaccine": "bcg", "dose": 1, "status": "skipped"},
                ]
            },
        ),
        _ctx(),
    )
    vaccines = {(t["vaccine"], t["dose"]) for t in r.outputs["todos"]}
    assert ("hepb", 1) not in vaccines
    assert ("bcg", 1) not in vaccines
    # 其余剂次仍在。
    assert ("hepb", 2) in vaccines


async def test_golden_vaccine_far_future_planned(vaccine_module: VaccineRuleModule):
    """出生 0 天：麻腮风第1剂（推荐 240 天）远期 → planned，无提醒（info）。"""
    r = await vaccine_module.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    mmr1 = _todo_for(r.outputs["todos"], "mmr", 1)
    assert mmr1["status"] == "planned"
    assert mmr1["alert_level"] == "info"
    assert mmr1["days_offset"] == 240
