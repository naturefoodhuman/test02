# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import CaseGraph, GraphEdge, GraphNode, Hypothesis
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.repositories import ArtifactRepository

from .confidence import compute_confidence
from .validators import ensure_not_fact


class HypothesisManager:
    def __init__(self, repository: ArtifactRepository | None = None, id_generator: FEOSIdGenerator | None = None):
        self.repository = repository
        self.ids = id_generator or FEOSIdGenerator()

    def create(self, case_id: str, statement: str, supports: list[str] | None = None, refutes: list[str] | None = None) -> Hypothesis:
        supports = supports or []
        refutes = refutes or []
        hyp = Hypothesis(id=self.ids.next("hyp"), case_id=case_id, statement=statement, supports=supports, refutes=refutes, confidence=compute_confidence(len(supports), len(refutes)))
        ensure_not_fact(hyp)
        return hyp

    def save_all(self, case_id: str, hypotheses: list[Hypothesis]) -> None:
        if self.repository:
            self.repository.put_yaml(case_id, "hypotheses", {"hypotheses": [h.to_dict() for h in hypotheses]})

    def sync_graph(self, graph: CaseGraph, hypothesis: Hypothesis) -> CaseGraph:
        graph.nodes.append(GraphNode(id=hypothesis.id, type="hypothesis", label=hypothesis.statement, ref_id=hypothesis.id, data={"confidence": hypothesis.confidence}))
        for ev_id in hypothesis.supports:
            graph.edges.append(GraphEdge(source=ev_id, target=hypothesis.id, type="supports", confidence=hypothesis.confidence))
        for ev_id in hypothesis.refutes:
            graph.edges.append(GraphEdge(source=ev_id, target=hypothesis.id, type="refutes", confidence=1.0 - hypothesis.confidence))
        return graph
