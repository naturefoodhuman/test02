# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 03:35:00


"""APC-T022 Vaccine planner golden tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.vaccine import VaccineRuleModule
from server.app.rule_engine.loader import load_rule_pack


def _module() -> VaccineRuleModule:
    return VaccineRuleModule(load_rule_pack(Path("config/rules/vaccine/cn-nip-2024.yaml")))


def test_vaccine_golden_cases() -> None:
    cases = yaml.safe_load(Path("tests/golden/rules/vaccine_cases.yaml").read_text())["cases"]
    module = _module()
    for case in cases:
        result = module.evaluate(RuleInput(domain="vaccine", payload=case["input"]))
        status_by_key = {item["vaccine_key"]: item["status"] for item in result.outputs["planned"]}
        for vaccine_key, expected_status in case["expect"].items():
            assert status_by_key[vaccine_key] == expected_status, case["name"]
        assert result.reason_code == "vaccine_plan_generated"
        assert result.evidence


def test_vaccine_requires_birth_date() -> None:
    result = _module().evaluate(RuleInput(domain="vaccine", payload={}))

    assert result.verdict == "block"
    assert result.reason_code == "birth_date_required"
