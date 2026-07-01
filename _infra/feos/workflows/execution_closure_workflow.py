# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.distillation import KnowledgeDistillationService, KnowledgeWriter
from _infra.feos.execution import OutcomeEvaluator
from _infra.feos.models import EscalationCase
from _infra.feos.repositories import KnowledgeRepository
from _infra.feos.storage import FEOSWorkspace


class ExecutionClosureWorkflow:
    def __init__(self, workspace: FEOSWorkspace):
        self.workspace = workspace

    def outcome_and_distill(self, case: EscalationCase, status: str, summary: str, plan_id: str | None = None):
        outcome = OutcomeEvaluator().record(case.id, status, summary, plan_id=plan_id)
        candidate = KnowledgeDistillationService(KnowledgeWriter(KnowledgeRepository(self.workspace))).distill(case, outcome, [])
        return {"outcome": outcome, "candidate": candidate}
