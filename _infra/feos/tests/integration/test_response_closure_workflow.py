# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.case_manager import CaseService, CreateCaseInput
from _infra.feos.repositories import CaseRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace
from _infra.feos.workflows import ExecutionClosureWorkflow, ResponseProcessingWorkflow


def test_response_closure_workflow(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    case = CaseService(CaseRepository(ws), TimelineRepository(ws)).create_case(CreateCaseInput(title="fixture", user_goal="debug issue"))
    raw = "## Claims\nRoot cause\n## Recommendations\n- Add tests\n"
    processed = ResponseProcessingWorkflow(ws).import_parse_verify_plan(case.id, raw)
    assert processed["response"].content_hash.startswith("sha256:")
    assert processed["parsed"].recommendations
    assert processed["verification"].status in {"passed", "warning"}
    assert processed["plan"] is not None
    closed = ExecutionClosureWorkflow(ws).outcome_and_distill(case, "resolved", "fixed", plan_id=processed["plan"].id)
    assert closed["candidate"].status == "captured"
