# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import KnowledgeCandidate
from _infra.feos.repositories import KnowledgeRepository


class KnowledgeWriter:
    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository

    def write(self, candidate: KnowledgeCandidate) -> str:
        path = self.repository.put_yaml(candidate.case_id, "candidates", {"candidates": [candidate.to_dict()]})
        self.repository.put_yaml(candidate.case_id, "distilled", {"knowledge": [candidate.to_dict()]})
        return str(path)
