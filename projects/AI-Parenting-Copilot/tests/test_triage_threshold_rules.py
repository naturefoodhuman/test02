# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:50:00


"""APC-T021 Triage and threshold rule golden tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from server.app.rule_engine.domain.models import RuleInput
from server.app.rule_engine.domains.thresholds import ThresholdRuleModule
from server.app.rule_engine.domains.triage import TriageRuleModule
from server.app.rule_engine.loader import load_rule_pack


def test_triage_and_threshold_golden_cases() -> None:
    triage = TriageRuleModule(load_rule_pack(Path("config/rules/triage/base.yaml")))
    thresholds = ThresholdRuleModule(load_rule_pack(Path("config/alert_thresholds.yaml")))
    modules = {"triage": triage, "thresholds": thresholds}
    cases = yaml.safe_load(Path("tests/golden/rules/triage_cases.yaml").read_text())["cases"]

    for case in cases:
        module = modules[case["domain"]]
        result = module.evaluate(RuleInput(domain=case["domain"], payload=case["input"]))
        expected = case["expect"]
        assert result.verdict == expected["verdict"], case["name"]
        assert result.reason_code == expected["reason_code"], case["name"]
        if "alert_level" in expected:
            assert result.outputs["alert_level"] == expected["alert_level"]


def test_threshold_requires_dual_condition() -> None:
    thresholds = ThresholdRuleModule(load_rule_pack(Path("config/alert_thresholds.yaml")))

    result = thresholds.evaluate(
        RuleInput(
            domain="thresholds",
            payload={
                "source": "manual",
                "requested_level": "yellow",
                "consecutive_days": 1,
                "deviation_percent": 50,
            },
        )
    )

    assert result.verdict == "allow"
    assert result.outputs["alert_level"] == "none"
