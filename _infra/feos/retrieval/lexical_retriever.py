# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import EscalationCase

from .feature_extractor import tokens
from .ranker import rank_similarity
from .service_models import SimilarityResult


class LexicalRetriever:
    def search(self, query: str, cases: list[EscalationCase], limit: int = 5) -> list[SimilarityResult]:
        q = tokens(query)
        results = []
        for case in cases:
            text = " ".join([case.title, case.problem.user_goal, case.problem.actual_behavior or "", case.problem.failure_signature or ""])
            score = rank_similarity(q, tokens(text))
            if score > 0:
                results.append(SimilarityResult(case_id=case.id, score=round(score, 4), reason="lexical_overlap"))
        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]
