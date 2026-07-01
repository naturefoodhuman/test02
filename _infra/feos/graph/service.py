# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""CaseGraph service."""

from __future__ import annotations

from _infra.feos.models import CaseGraph, Evidence
from _infra.feos.repositories import GraphRepository

from .builder import CaseGraphBuilder


class CaseGraphService:
    def __init__(self, repository: GraphRepository, builder: CaseGraphBuilder | None = None):
        self.repository = repository
        self.builder = builder or CaseGraphBuilder()

    def build_and_save(self, case_id: str, evidence: list[Evidence]) -> CaseGraph:
        graph = self.builder.build(case_id, evidence)
        self.repository.put_json(case_id, "graph", graph.to_dict())
        return graph
