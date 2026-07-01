# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import EscalationCase
from _infra.feos.repositories import ArtifactRepository

from .lexical_retriever import LexicalRetriever
from .service_models import SimilarityResult


class SimilarityRetrievalService:
    def __init__(self, repository: ArtifactRepository | None = None, lexical: LexicalRetriever | None = None):
        self.repository = repository
        self.lexical = lexical or LexicalRetriever()

    def search(self, query: str, previous_cases: list[EscalationCase], case_id: str | None = None, limit: int = 5) -> list[SimilarityResult]:
        results = self.lexical.search(query, previous_cases, limit=limit)
        if self.repository and case_id is not None:
            self.repository.put_yaml(case_id, "similar_cases", {"results": [r.to_dict() for r in results]})
        return results
