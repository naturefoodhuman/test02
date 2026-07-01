# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import EscalationCase, KnowledgeCandidate, Outcome
from .candidate_extractor import KnowledgeCandidateExtractor
from .knowledge_writer import KnowledgeWriter


class KnowledgeDistillationService:
    def __init__(self, writer: KnowledgeWriter, extractor: KnowledgeCandidateExtractor | None = None):
        self.writer = writer
        self.extractor = extractor or KnowledgeCandidateExtractor()

    def distill(self, case: EscalationCase, outcome: Outcome, evidence_refs: list[str] | None = None) -> KnowledgeCandidate | None:
        candidate = self.extractor.extract(case, outcome, evidence_refs)
        if candidate:
            self.writer.write(candidate)
        return candidate
