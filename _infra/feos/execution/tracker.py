# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.errors import FEOSPolicyError
from _infra.feos.models import ExecutionPlan


class ExecutionTracker:
    def mark_step_completed(self, plan: ExecutionPlan, step_id: str) -> ExecutionPlan:
        if not plan.approved:
            raise FEOSPolicyError("unapproved plan cannot execute")
        for step in plan.steps:
            if step.id == step_id:
                step.status = "completed"
        return plan
