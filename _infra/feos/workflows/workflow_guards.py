# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Workflow-level guard checks."""

from __future__ import annotations

from _infra.feos.errors import FEOSError
from _infra.feos.models.enums import CaseStatus


class WorkflowGuardError(FEOSError):
    """Workflow operation is not allowed for current state/context."""


class WorkflowGuard:
    def ensure_export_allowed(self, status: CaseStatus | str) -> None:
        st = CaseStatus(status)
        allowed = {CaseStatus.PACKAGE_GENERATED, CaseStatus.WAITING_HUMAN_EXPORT}
        if st not in allowed:
            raise WorkflowGuardError("export requires PackageGenerated or WaitingHumanExport")

    def ensure_execute_allowed(self, status: CaseStatus | str, approved_plan: bool) -> None:
        if CaseStatus(status) == CaseStatus.ARCHIVED:
            raise WorkflowGuardError("archived cases cannot execute")
        if not approved_plan:
            raise WorkflowGuardError("execution requires approved plan")

    def ensure_not_archived(self, status: CaseStatus | str) -> None:
        if CaseStatus(status) == CaseStatus.ARCHIVED:
            raise WorkflowGuardError("archived cases cannot continue workflow")
