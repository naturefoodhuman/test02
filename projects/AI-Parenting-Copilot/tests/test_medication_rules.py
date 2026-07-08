# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:50:00


"""APC-T020 Medication rule golden tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.medication import MedicationRuleModule
from server.app.rule_engine.loader import load_rule_pack


def _module() -> MedicationRuleModule:
    return MedicationRuleModule(load_rule_pack(Path("config/rules/medication/base.yaml")))


def test_medication_golden_cases() -> None:
    cases = yaml.safe_load(Path("tests/golden/rules/medication_cases.yaml").read_text())["cases"]
    module = _module()
    for case in cases:
        result = module.evaluate(RuleInput(domain="medication", payload=case["input"]))
        expected = case["expect"]
        assert result.verdict == expected["verdict"], case["name"]
        assert result.reason_code == expected["reason_code"], case["name"]
        if "dose_mg" in expected:
            assert result.outputs["dose_mg"] == expected["dose_mg"]
            assert "dose_ml" in result.outputs


def test_missing_concentration_outputs_no_ml_dose() -> None:
    result = _module().evaluate(
        RuleInput(
            domain="medication",
            payload={"medication_key": "acetaminophen", "baby_age_months": 4, "weight_kg": 6},
        )
    )

    assert result.verdict == "block"
    assert result.reason_code == "concentration_required"
    assert "dose_ml" not in result.outputs
