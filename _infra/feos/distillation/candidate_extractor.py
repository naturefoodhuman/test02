# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import EscalationCase, KnowledgeCandidate, Outcome
from _infra.feos.models.ids import FEOSIdGenerator


class KnowledgeCandidateExtractor:
    def __init__(self, id_generator: FEOSIdGenerator | None = None):
        self.ids = id_generator or FEOSIdGenerator()

    def extract(self, case: EscalationCase, outcome: Outcome, evidence_refs: list[str] | None = None) -> KnowledgeCandidate | None:
        if outcome.status not in {"resolved", "unresolved"}:
            return None
        confidence = "high" if outcome.status == "resolved" else "low"
        return KnowledgeCandidate(id=self.ids.next("kc"), case_id=case.id, title=f"Lesson from {case.title}", content=f"Outcome: {outcome.summary}\nConfidence: {confidence}", source_refs=evidence_refs or [], tags=[outcome.status])
