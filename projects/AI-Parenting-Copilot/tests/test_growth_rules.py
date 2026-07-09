# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 03:35:00


"""APC-T023 Growth rule golden tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.growth import GrowthRuleModule
from server.app.rule_engine.loader import load_rule_pack


def _module() -> GrowthRuleModule:
    return GrowthRuleModule(load_rule_pack(Path("config/rules/growth/who-0-5.yaml")))


def test_growth_golden_cases() -> None:
    cases = yaml.safe_load(Path("tests/golden/rules/growth_cases.yaml").read_text())["cases"]
    module = _module()
    for case in cases:
        result = module.evaluate(RuleInput(domain="growth", payload=case["input"]))
        assert result.outputs["percentile_band"] == case["expect"]["percentile_band"], case["name"]
        assert result.outputs["alert_level"] == case["expect"]["alert_level"], case["name"]
        assert result.reason_code == "growth_percentile_estimated"
        assert result.evidence


def test_growth_requires_fields_and_never_strong_alerts_single_point() -> None:
    module = _module()
    missing = module.evaluate(RuleInput(domain="growth", payload={"sex": "male"}))
    single = module.evaluate(
        RuleInput(
            domain="growth",
            payload={"sex": "male", "age_months": 3, "metric": "weight_kg", "value": 8.5},
        )
    )

    assert missing.verdict == "block"
    assert single.outputs["alert_level"] == "none"
