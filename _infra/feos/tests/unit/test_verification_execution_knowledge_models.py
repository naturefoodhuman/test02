# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import (
    ExecutionPlan,
    ExecutionStep,
    KnowledgeCandidate,
    Outcome,
    ParsedClaim,
    ParsedResponse,
    Recommendation,
    VerificationCheckResult,
    VerificationResult,
)


def test_parsed_response_models():
    parsed = ParsedResponse(
        id="parsed_001",
        case_id="case_001",
        response_id="resp_001",
        claims=[ParsedClaim(id="claim_001", text="schema mismatch", evidence_refs=["ev1"])],
        recommendations=[Recommendation(id="rec_001", text="add result field")],
    )
    assert parsed.claims[0].evidence_refs == ["ev1"]
    assert parsed.recommendations[0].requires_verification is True


def test_verification_result_models():
    result = VerificationResult(
        id="ver_001",
        case_id="case_001",
        parsed_response_id="parsed_001",
        checks=[VerificationCheckResult(check_id="evidence_alignment", status="passed")],
        status="passed",
    )
    assert result.status == "passed"
    assert result.checks[0].check_id == "evidence_alignment"


def test_execution_plan_and_outcome_models():
    plan = ExecutionPlan(
        id="plan_001",
        case_id="case_001",
        verification_id="ver_001",
        steps=[ExecutionStep(id="step_001", description="edit file", requires_approval=True)],
    )
    assert plan.steps[0].requires_approval is True
    outcome = Outcome(id="outcome_001", case_id="case_001", plan_id="plan_001", status="resolved", summary="fixed")
    assert outcome.status == "resolved"


def test_knowledge_candidate_lifecycle_status():
    candidate = KnowledgeCandidate(id="kc_001", case_id="case_001", title="Schema mismatch lesson", content="Always validate output contract")
    assert candidate.status == "captured"
    candidate.status = "verified"
    assert candidate.status == "verified"
