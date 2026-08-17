# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""VaccineRuleModule 单元测试（APC-T022）。

用测试专用 RulePack 验证疫苗规划各分支：到期/逾期/已接种排除/跳过排除/
records 两种形式/排序/region。不依赖 DB（纯内存求值）。asyncio_mode=auto。
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
from server.app.rule_engine.domains.vaccine import VaccineRuleModule

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


def _pack() -> RulePack:
    """测试专用疫苗规则包（3 个剂次：v1@0d / v2@30d / v3@180d）。"""
    return RulePack(
        policy_type="vaccine",
        region="CN",
        version=1,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id="v1",
                conditions=[RuleCondition(op="eq", field="variables.vaccine", value="v:1")],
                action=RuleAction(
                    verdict="info",
                    outputs={"recommended_age_days": 0, "dose": 1, "is_nip": True},
                    reason_code="v1",
                    evidence_text="v1",
                ),
            ),
            Rule(
                rule_id="v2",
                conditions=[RuleCondition(op="eq", field="variables.vaccine", value="v:2")],
                action=RuleAction(
                    verdict="info",
                    outputs={"recommended_age_days": 30, "dose": 2, "is_nip": True},
                    reason_code="v2",
                    evidence_text="v2",
                ),
            ),
            Rule(
                rule_id="v3",
                conditions=[RuleCondition(op="eq", field="variables.vaccine", value="v:3")],
                action=RuleAction(
                    verdict="info",
                    outputs={"recommended_age_days": 180, "dose": 3, "is_nip": False},
                    reason_code="v3",
                    evidence_text="v3",
                ),
            ),
        ],
    )


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, region="CN", now=NOW)


def _todo(todos, vaccine, dose):
    for t in todos:
        if t["vaccine"] == vaccine and t["dose"] == dose:
            return t
    raise AssertionError(f"todo not found: {vaccine}:{dose}")


async def test_vaccine_newborn_due_today():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    t = _todo(r.outputs["todos"], "v", 1)
    assert t["status"] == "due"
    assert t["alert_level"] == "blue"
    assert t["days_offset"] == 0
    assert t["is_nip"] is True


async def test_vaccine_upcoming():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=16, variables={}), _ctx())
    t = _todo(r.outputs["todos"], "v", 2)
    assert t["status"] == "upcoming"
    assert t["days_offset"] == 14


async def test_vaccine_due_soon():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=27, variables={}), _ctx())
    t = _todo(r.outputs["todos"], "v", 2)
    assert t["status"] == "due_soon"
    assert t["days_offset"] == 3


async def test_vaccine_overdue_blue():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=33, variables={}), _ctx())
    t = _todo(r.outputs["todos"], "v", 2)
    assert t["status"] == "overdue"
    assert t["alert_level"] == "blue"
    assert t["days_offset"] == -3


async def test_vaccine_overdue_yellow():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=195, variables={}), _ctx())
    t = _todo(r.outputs["todos"], "v", 3)
    assert t["status"] == "overdue"
    assert t["alert_level"] == "yellow"
    assert t["days_offset"] == -15


async def test_vaccine_completed_excluded():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"vaccine_records": [{"vaccine": "v", "dose": 1, "status": "completed"}]},
        ),
        _ctx(),
    )
    keys = {(t["vaccine"], t["dose"]) for t in r.outputs["todos"]}
    assert ("v", 1) not in keys
    assert ("v", 2) in keys


async def test_vaccine_skipped_excluded():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"vaccine_records": [{"vaccine": "v", "dose": 1, "status": "skipped"}]},
        ),
        _ctx(),
    )
    keys = {(t["vaccine"], t["dose"]) for t in r.outputs["todos"]}
    assert ("v", 1) not in keys


async def test_vaccine_delayed_still_in_todos():
    """delayed 状态（未完成但已记录延迟）仍出现在待办（未 completed/skipped）。"""
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"vaccine_records": [{"vaccine": "v", "dose": 1, "status": "delayed"}]},
        ),
        _ctx(),
    )
    keys = {(t["vaccine"], t["dose"]) for t in r.outputs["todos"]}
    assert ("v", 1) in keys


async def test_vaccine_records_dict_form():
    """vaccine_records 支持 dict 形式（key=vaccine:dose）。"""
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(
        RuleInput(
            baby_age_days=0,
            variables={"vaccine_records": {"v:1": "completed"}},
        ),
        _ctx(),
    )
    keys = {(t["vaccine"], t["dose"]) for t in r.outputs["todos"]}
    assert ("v", 1) not in keys
    assert ("v", 2) in keys


async def test_vaccine_todos_sorted_by_days_offset():
    """待办按 days_offset 升序（最紧迫在前）。"""
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    offsets = [t["days_offset"] for t in r.outputs["todos"]]
    assert offsets == sorted(offsets)
    # v1（0d）最紧迫，应在最前。
    assert r.outputs["todos"][0]["vaccine"] == "v"
    assert r.outputs["todos"][0]["dose"] == 1


async def test_vaccine_region_from_ctx():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    assert r.outputs["region"] == "CN"


async def test_vaccine_region_from_variables_override():
    """variables.vaccine_region 覆盖 ctx.region（与 baby.vaccine_region 对齐）。"""
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=0, variables={"vaccine_region": "US"}), _ctx())
    assert r.outputs["region"] == "US"


async def test_vaccine_evidence_carries_policy_version():
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    assert r.evidence[0].policy_version == 1
    assert r.evidence[0].rule_id == "vaccine"


async def test_vaccine_self_paid_flag():
    """自费疫苗（is_nip=False）仍产出待办，标记 is_nip=False。"""
    m = VaccineRuleModule(_pack())
    r = await m.evaluate(RuleInput(baby_age_days=0, variables={}), _ctx())
    t = _todo(r.outputs["todos"], "v", 3)
    assert t["is_nip"] is False
