# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""MedicationRuleModule 单元测试（APC-T020）。

用测试专用 RulePack（真实参数 mg_per_kg=10 等）验证校验链路各分支：
未知体重/体重过旧/月龄禁忌/占位参数/未知浓度/给药间隔/24h 上限/allow。
不依赖 DB（纯内存求值）。asyncio_mode=auto。

注：config/rules/medication/base-1.yaml 为占位参数（mg_per_kg=0），
生产行为是 params_pending block；本测试用真实参数包验证计算逻辑（allow/间隔/24h/浓度）。
golden 测试覆盖占位包的生产行为。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from server.app.rule_engine.domain.models import (
    Rule,
    RuleAction,
    RuleCondition,
    RuleContext,
    RuleInput,
    RulePack,
)
from server.app.rule_engine.domains.medication import MedicationRuleModule

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


def _pack(
    *,
    mg_per_kg: float = 10.0,
    min_age_months: int = 6,
    interval_hours: float = 6.0,
    max_24h_mg_per_kg: float = 40.0,
    max_single_dose_mg: float = 0.0,
    drug: str = "ibuprofen",
) -> RulePack:
    """测试专用规则包（真实参数，非占位）。"""
    return RulePack(
        policy_type="medication",
        region="CN",
        version=1,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id=f"{drug}_params",
                conditions=[RuleCondition(op="eq", field="variables.drug", value=drug)],
                action=RuleAction(
                    verdict="info",
                    outputs={
                        "mg_per_kg": mg_per_kg,
                        "min_age_months": min_age_months,
                        "interval_hours": interval_hours,
                        "max_24h_mg_per_kg": max_24h_mg_per_kg,
                        "max_single_dose_mg": max_single_dose_mg,
                    },
                    reason_code=f"{drug}_params",
                    evidence_text="test",
                ),
            )
        ],
    )


def _ctx(now: datetime | None = None) -> RuleContext:
    return RuleContext(policy_version=1, now=now or NOW)


# ---- 未知体重 ----


async def test_unknown_weight_blocks():
    mod = MedicationRuleModule(_pack())
    r = await mod.evaluate(
        RuleInput(baby_age_days=200, variables={"drug": "ibuprofen", "concentration_mg_ml": 50}),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "unknown_weight"
    assert r.outputs == {}  # 不出剂量。


# ---- 体重过旧 ----


async def test_stale_weight_warns():
    mod = MedicationRuleModule(_pack())
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "weight_age_days": 10},
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.reason_code == "weight_stale"


async def test_fresh_weight_proceeds():
    """体重 age ≤ 7 天不触发 weight_stale。"""
    mod = MedicationRuleModule(_pack())
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "weight_age_days": 7},
        ),
        _ctx(),
    )
    assert r.reason_code != "weight_stale"


# ---- 月龄禁忌 ----


async def test_under_min_age_blocks():
    """<6 月龄（180 天）布洛芬 → block。"""
    mod = MedicationRuleModule(_pack(min_age_months=6))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=150,
            weight_kg=5,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "under_min_age"


async def test_under_min_age_doctor_override_warns():
    """<6 月龄 + doctor_override → warn（医生已明确要求）。"""
    mod = MedicationRuleModule(_pack(min_age_months=6))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=150,
            weight_kg=5,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "doctor_override": True},
        ),
        _ctx(),
    )
    assert r.verdict == "warn"
    assert r.reason_code == "doctor_override_under_min_age"


async def test_at_min_age_proceeds():
    """满 6 月龄（180 天）不触发 under_min_age。"""
    mod = MedicationRuleModule(_pack(min_age_months=6))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=180,
            weight_kg=8,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.reason_code != "under_min_age"


# ---- 占位参数 ----


async def test_placeholder_params_blocks():
    """mg_per_kg=0（占位）→ block params_pending。"""
    mod = MedicationRuleModule(_pack(mg_per_kg=0.0))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "params_pending"
    assert r.outputs == {}


# ---- 未知浓度 ----


async def test_unknown_concentration_blocks_no_ml():
    """未知浓度 → block，不出 ml（但 dose_mg 已可输出）。"""
    mod = MedicationRuleModule(_pack())
    r = await mod.evaluate(
        RuleInput(baby_age_days=200, weight_kg=10, variables={"drug": "ibuprofen"}),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "unknown_concentration"
    assert "dose_mg" in r.outputs  # mg 已算（10 mg/kg × 10 kg = 100）。
    assert r.outputs["dose_mg"] == 100.0
    assert "dose_ml" not in r.outputs  # 不出 ml。


# ---- 给药间隔 ----


async def test_interval_too_short_blocks():
    """距上次给药 < interval_hours → block。"""
    mod = MedicationRuleModule(_pack(interval_hours=6.0))
    last = NOW - timedelta(hours=2)
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "last_dose_at": last},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "interval_too_short"


async def test_interval_ok_proceeds():
    """距上次给药 ≥ interval_hours → 继续。"""
    mod = MedicationRuleModule(_pack(interval_hours=6.0))
    last = NOW - timedelta(hours=7)
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "last_dose_at": last},
        ),
        _ctx(),
    )
    assert r.reason_code != "interval_too_short"


# ---- 24h 上限 ----


async def test_near_24h_limit_blocks():
    """24h 累计 + 本次 ≥ max_24h × 0.9 → block。"""
    # max_24h_mg_per_kg=40, weight=10 → max_24h=400mg；本次 dose_mg=100。
    # given_24h=310 → 310+100=410 ≥ 400×0.9=360 → block。
    mod = MedicationRuleModule(_pack(max_24h_mg_per_kg=40.0))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "given_24h_mg": 310},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "near_24h_limit"


async def test_under_24h_limit_proceeds():
    """24h 累计 + 本次 < max_24h × 0.9 → 继续。"""
    mod = MedicationRuleModule(_pack(max_24h_mg_per_kg=40.0))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50, "given_24h_mg": 100},
        ),
        _ctx(),
    )
    assert r.reason_code != "near_24h_limit"


# ---- allow + 计算 ----


async def test_allow_outputs_dose_mg_and_ml():
    """全校验通过 → allow，产出 dose_mg + dose_ml。"""
    mod = MedicationRuleModule(_pack(mg_per_kg=10.0))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "allow"
    assert r.reason_code == "ok"
    assert r.outputs["dose_mg"] == 100.0  # 10 mg/kg × 10 kg。
    assert r.outputs["dose_ml"] == 2.0  # 100 mg / 50 mg/ml。
    assert r.rule_version == "medication@1"
    assert len(r.evidence) == 1
    assert r.evidence[0].policy_version == 1


async def test_max_single_dose_caps_mg():
    """max_single_dose_mg 上限封顶 dose_mg。"""
    mod = MedicationRuleModule(_pack(mg_per_kg=10.0, max_single_dose_mg=50.0))
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "allow"
    assert r.outputs["dose_mg"] == 50.0  # 100 被封顶 50。
    assert r.outputs["dose_ml"] == 1.0  # 50 / 50。


# ---- 未知药物 ----


async def test_unknown_drug_blocks():
    mod = MedicationRuleModule(_pack())
    r = await mod.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "unknown", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "unknown_drug"


async def test_missing_drug_blocks():
    mod = MedicationRuleModule(_pack())
    r = await mod.evaluate(
        RuleInput(baby_age_days=200, weight_kg=10, variables={"concentration_mg_ml": 50}),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "unknown_drug"
