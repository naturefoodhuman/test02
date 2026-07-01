# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Build a deterministic CaseGraph from Evidence."""

from __future__ import annotations

from _infra.feos.models import CaseGraph, Evidence, GraphEdge, GraphNode


class CaseGraphBuilder:
    def build(self, case_id: str, evidence: list[Evidence]) -> CaseGraph:
        graph = CaseGraph(id=f"graph_{case_id}", case_id=case_id)
        graph.nodes.append(GraphNode(id=case_id, type="case", label=case_id, ref_id=case_id))
        seen_edges = set()
        for ev in sorted(evidence, key=lambda item: item.id):
            graph.nodes.append(GraphNode(id=ev.id, type="evidence", label=ev.subtype or str(ev.type), ref_id=ev.id, data={"importance": ev.quality.importance}))
            fact_id = f"fact_{ev.id}"
            graph.nodes.append(GraphNode(id=fact_id, type="fact", label=ev.content.text_preview or ev.id, ref_id=ev.id))
            edge = (ev.id, fact_id, "supports")
            if edge not in seen_edges:
                graph.edges.append(GraphEdge(source=ev.id, target=fact_id, type="supports", confidence=ev.quality.confidence))
                seen_edges.add(edge)
            edge2 = (case_id, ev.id, "relates")
            if edge2 not in seen_edges:
                graph.edges.append(GraphEdge(source=case_id, target=ev.id, type="relates", confidence=1.0))
                seen_edges.add(edge2)
        return graph
