# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.case_manager import CaseService, CreateCaseInput
from _infra.feos.observability import diagnose_case
from _infra.feos.repositories import CaseRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace


def test_diagnostics_healthy_and_missing_case(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    case = CaseService(CaseRepository(ws), TimelineRepository(ws)).create_case(CreateCaseInput(title="T", user_goal="debug"))
    report = diagnose_case(ws, case.id)
    assert report.ok is True
    missing = diagnose_case(ws, "missing")
    assert missing.ok is False
    assert "missing case.yaml" in missing.errors
