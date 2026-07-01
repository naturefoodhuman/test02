# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ExecutionPlan, ExecutionStep, ParsedResponse, VerificationResult
from _infra.feos.models.ids import FEOSIdGenerator


class ExecutionPlanner:
    def __init__(self, id_generator: FEOSIdGenerator | None = None):
        self.ids = id_generator or FEOSIdGenerator()

    def plan(self, parsed: ParsedResponse, verification: VerificationResult) -> ExecutionPlan | None:
        if verification.status == "failed":
            return None
        steps = [ExecutionStep(id=self.ids.next("step"), description=rec.text, requires_approval=True) for rec in parsed.recommendations]
        return ExecutionPlan(id=self.ids.plan_id(), case_id=parsed.case_id, verification_id=verification.id, steps=steps, approved=False)
