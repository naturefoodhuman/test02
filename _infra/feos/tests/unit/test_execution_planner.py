# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.execution import ExecutionService
from _infra.feos.models import ParsedResponse, Recommendation, VerificationResult
from _infra.feos.repositories import ExecutionRepository
from _infra.feos.storage import FEOSWorkspace, read_yaml


def test_execution_plan_created_only_for_non_failed_verification(tmp_path):
    parsed = ParsedResponse(id="p", case_id="case", response_id="r", recommendations=[Recommendation(id="rec", text="add test")])
    failed = VerificationResult(id="v1", case_id="case", parsed_response_id="p", status="failed")
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    service = ExecutionService(ExecutionRepository(ws))
    assert service.create_plan(parsed, failed) is None
    passed = VerificationResult(id="v2", case_id="case", parsed_response_id="p", status="passed")
    plan = service.create_plan(parsed, passed)
    assert plan.approved is False
    assert read_yaml(ws.root / "cases" / "case" / "execution" / f"{plan.id}.yaml")["id"] == plan.id
