# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.workflows import FEOSWorkflow, WorkflowGuard, WorkflowGuardError


def test_export_requires_package_generated():
    guard = WorkflowGuard()
    guard.ensure_export_allowed("PackageGenerated")
    with pytest.raises(WorkflowGuardError):
        guard.ensure_export_allowed("Created")


def test_execute_requires_approved_plan_and_not_archived():
    guard = WorkflowGuard()
    guard.ensure_execute_allowed("PlanningExecution", approved_plan=True)
    with pytest.raises(WorkflowGuardError):
        guard.ensure_execute_allowed("PlanningExecution", approved_plan=False)
    with pytest.raises(WorkflowGuardError):
        guard.ensure_execute_allowed("Archived", approved_plan=True)


def test_workflow_shell_uses_guard():
    workflow = FEOSWorkflow()
    assert workflow.prepare_clipboard_export("PackageGenerated") == "export_allowed"
    assert workflow.execute_plan("PlanningExecution", approved_plan=True) == "execute_allowed"
