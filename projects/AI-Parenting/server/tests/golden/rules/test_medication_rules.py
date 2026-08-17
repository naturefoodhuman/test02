# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""用药规则包黄金用例（APC-T020）。

加载 ``config/rules/medication/base-1.yaml``（占位参数包），验证生产行为：
占位参数（mg_per_kg=0）下，体重/月龄校验通过后 → ``block params_pending``（待医生确认，
不出剂量）。这反映安全关键铁律：系统不凭空编造医疗数值（PRD §11.11.1）。

计算逻辑（allow/间隔/24h/浓度）在 ``server/tests/unit/rule_engine/domains/test_medication.py``
用真实参数包覆盖（golden 用占位包验证生产行为，分工明确）。asyncio_mode=auto。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleInput
from server.app.rule_engine.domains.medication import MedicationRuleModule
from server.app.rule_engine.loader import load_pack

pytestmark = pytest.mark.golden

RULES_DIR = Path(__file__).resolve().parents[4] / "config" / "rules"
MEDICATION_PACK = RULES_DIR / "medication" / "base-1.yaml"

NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def medication_module() -> MedicationRuleModule:
    pack = load_pack(MEDICATION_PACK)
    return MedicationRuleModule(pack)


def _ctx() -> RuleContext:
    return RuleContext(policy_version=1, now=NOW)


async def test_golden_medication_placeholder_blocks(medication_module: MedicationRuleModule):
    """占位参数包：体重/月龄 OK 时 → block params_pending（生产行为，待医生确认）。"""
    r = await medication_module.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "params_pending"
    assert r.outputs == {}  # 不出剂量。
    assert r.rule_version == "medication@1"
    assert len(r.evidence) == 1


async def test_golden_medication_unknown_weight_blocks(medication_module: MedicationRuleModule):
    """未知体重 → block unknown_weight（占位参数包下体重校验仍优先）。"""
    r = await medication_module.evaluate(
        RuleInput(baby_age_days=200, variables={"drug": "ibuprofen", "concentration_mg_ml": 50}),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "unknown_weight"


async def test_golden_medication_under_min_age_blocks(medication_module: MedicationRuleModule):
    """<6 月龄布洛芬 → block under_min_age（占位参数包下月龄校验仍优先）。"""
    r = await medication_module.evaluate(
        RuleInput(
            baby_age_days=30,
            weight_kg=5,
            variables={"drug": "ibuprofen", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "under_min_age"


async def test_golden_medication_unknown_drug_blocks(medication_module: MedicationRuleModule):
    """未知药物 → block unknown_drug。"""
    r = await medication_module.evaluate(
        RuleInput(
            baby_age_days=200,
            weight_kg=10,
            variables={"drug": "unknown_drug", "concentration_mg_ml": 50},
        ),
        _ctx(),
    )
    assert r.verdict == "block"
    assert r.reason_code == "unknown_drug"
