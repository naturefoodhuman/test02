# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import Outcome
from _infra.feos.models.ids import FEOSIdGenerator


class OutcomeEvaluator:
    def __init__(self, id_generator: FEOSIdGenerator | None = None):
        self.ids = id_generator or FEOSIdGenerator()

    def record(self, case_id: str, status: str, summary: str, plan_id: str | None = None) -> Outcome:
        return Outcome(id=self.ids.next("outcome"), case_id=case_id, plan_id=plan_id, status=status, summary=summary)
