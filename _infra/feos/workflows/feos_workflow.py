# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS workflow shell.

The shell exposes guard-wrapped placeholders only. Business workflow steps are
implemented in later tasks.
"""

from __future__ import annotations

from .workflow_guards import WorkflowGuard


class FEOSWorkflow:
    def __init__(self, guard: WorkflowGuard | None = None):
        self.guard = guard or WorkflowGuard()

    def prepare_clipboard_export(self, status: str) -> str:
        self.guard.ensure_export_allowed(status)
        return "export_allowed"

    def execute_plan(self, status: str, approved_plan: bool) -> str:
        self.guard.ensure_execute_allowed(status, approved_plan=approved_plan)
        return "execute_allowed"
