# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ExecutionPlan, ParsedResponse, VerificationResult
from _infra.feos.repositories import ExecutionRepository
from .planner import ExecutionPlanner


class ExecutionService:
    def __init__(self, repository: ExecutionRepository, planner: ExecutionPlanner | None = None):
        self.repository = repository
        self.planner = planner or ExecutionPlanner()

    def create_plan(self, parsed: ParsedResponse, verification: VerificationResult) -> ExecutionPlan | None:
        plan = self.planner.plan(parsed, verification)
        if plan:
            self.repository.put_yaml(parsed.case_id, plan.id, plan.to_dict())
        return plan
