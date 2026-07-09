# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:50:00


"""APC-T018 Rule Engine kernel/loader/registry tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.app.common.errors import ConflictError
from server.app.rule_engine.domain.models import RuleInput, RuleResult, Verdict
from server.app.rule_engine.evidence_repo import InMemoryEvidencePolicyRepository
from server.app.rule_engine.loader import load_rule_pack, validate_rule_packs
from server.app.rule_engine.registry import RuleRegistry


class AllowModule:
    domain = "unit"
    rule_version = "unit-1"

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        return RuleResult.allow(domain=self.domain, rule_version=self.rule_version)


def test_rule_pack_loader_computes_hash_and_validates_all_packs() -> None:
    root = Path("config/rules")
    packs = validate_rule_packs(root)
    medication = load_rule_pack(root / "medication/base.yaml")

    assert {pack.domain for pack in packs} >= {"medication", "triage"}
    assert len(medication.compute_hash()) == 64
    assert medication.policy_type == "medication"


def test_registry_dispatches_by_domain_and_rejects_duplicate() -> None:
    registry = RuleRegistry()
    module = AllowModule()
    registry.register(module)

    result = registry.evaluate(RuleInput(domain="unit", payload={}))

    assert result.verdict == Verdict.ALLOW
    with pytest.raises(ConflictError):
        registry.register(module)


def test_in_memory_evidence_policy_activation_closes_old_current() -> None:
    repo = InMemoryEvidencePolicyRepository()
    pack = load_rule_pack(Path("config/rules/medication/base.yaml"))

    first = repo.activate(pack)
    second = repo.activate(pack)

    assert first.effective_to is not None
    assert second.effective_to is None
    assert repo.get_current("medication", "CN") is second
