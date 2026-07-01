# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ExecutionPlan


def approve_plan(plan: ExecutionPlan, actor: str = "human") -> ExecutionPlan:
    plan.approved = True
    return plan
