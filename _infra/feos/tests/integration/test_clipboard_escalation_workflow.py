# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.case_manager import CaseService, CreateCaseInput
from _infra.feos.repositories import CaseRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace
from _infra.feos.workflows import ClipboardEscalationWorkflow


def test_clipboard_escalation_workflow_generates_export(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    case = CaseService(CaseRepository(ws), TimelineRepository(ws)).create_case(CreateCaseInput(title="fixture", user_goal="debug issue"))
    result = ClipboardEscalationWorkflow(ws, tmp_path).run_until_export(case)
    export_path = ws.root / "cases" / case.id / "exports" / "clipboard.md"
    assert export_path.exists()
    assert "External Reasoning Request" in export_path.read_text()
    assert result["package"].case_id == case.id
