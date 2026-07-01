# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from datetime import UTC, datetime

from _infra.feos.errors import FEOSError, FEOSPolicyError, FEOSStateError, FEOSStorageError, FEOSVerificationError
from _infra.feos.models.enums import ARCHITECTURE_CASE_STATUSES, CaseStatus
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.models.result import ServiceResult

EXPECTED_STATUSES = [
    "Draft", "Created", "CollectingEvidence", "GraphBuilding", "Investigating", "PolicyChecking",
    "ContextCompiling", "PackageGenerated", "WaitingHumanExport", "WaitingExternalResponse",
    "ResponseImported", "ParsingResponse", "Verifying", "PlanningExecution", "Executing",
    "EvaluatingOutcome", "Resolved", "Unresolved", "Abandoned", "DistillingKnowledge", "Archived",
]


def test_case_statuses_match_architecture():
    assert ARCHITECTURE_CASE_STATUSES == EXPECTED_STATUSES
    assert [status.value for status in CaseStatus] == EXPECTED_STATUSES


def test_id_format_and_determinism():
    fixed = lambda: datetime(2026, 7, 1, tzinfo=UTC)
    gen = FEOSIdGenerator(clock=fixed)
    assert gen.case_id() == "case_2026_07_01_001"
    assert gen.case_id() == "case_2026_07_01_002"
    assert gen.evidence_id("ev_stacktrace") == "ev_stacktrace_2026_07_01_001"


def test_error_hierarchy():
    for cls in [FEOSStateError, FEOSStorageError, FEOSPolicyError, FEOSVerificationError]:
        assert issubclass(cls, FEOSError)


def test_service_result_success_and_failure():
    ok = ServiceResult.success(value={"x": 1}, warnings=["minor"])
    assert ok.ok is True
    assert ok.value == {"x": 1}
    assert ok.warnings == ["minor"]

    failed = ServiceResult.failure("bad")
    assert failed.ok is False
    assert failed.errors == ["bad"]
