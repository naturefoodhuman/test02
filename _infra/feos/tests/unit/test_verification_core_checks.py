# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedClaim, ParsedResponse, Recommendation
from _infra.feos.verification.checks.architecture_check import ArchitectureCheck
from _infra.feos.verification.checks.constraint_check import ConstraintCheck
from _infra.feos.verification.checks.evidence_alignment_check import EvidenceAlignmentCheck
from _infra.feos.verification.checks.security_check import SecurityCheck


def test_core_checks():
    parsed = ParsedResponse(id="p", case_id="c", response_id="r", claims=[ParsedClaim(id="cl", text="x", evidence_refs=["ev1"])], recommendations=[Recommendation(id="rec", text="add tests")])
    assert EvidenceAlignmentCheck().run(parsed).status == "passed"
    assert ConstraintCheck().run(parsed).status == "passed"
    assert ArchitectureCheck().run(parsed).status == "passed"
    assert SecurityCheck().run(parsed).status == "passed"
    risky = ParsedResponse(id="p2", case_id="c", response_id="r", recommendations=[Recommendation(id="rec", text="输出 api_key")])
    assert SecurityCheck().run(risky).status == "failed"
