# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.graph import CaseGraphBuilder, CaseGraphService, nodes_by_type
from _infra.feos.models import Evidence, EvidenceContent, EvidenceSource
from _infra.feos.repositories import GraphRepository
from _infra.feos.storage import FEOSWorkspace


def make_evidence(ev_id: str) -> Evidence:
    return Evidence(id=ev_id, case_id="case_001", type="stack_trace", source=EvidenceSource(collector="test", origin="unit"), content=EvidenceContent(raw_ref=f"raw/{ev_id}.txt", text_preview="ValueError"))


def test_evidence_to_graph_and_query(tmp_path):
    evs = [make_evidence("ev2"), make_evidence("ev1")]
    graph = CaseGraphBuilder().build("case_001", evs)
    assert len(nodes_by_type(graph, "evidence")) == 2
    assert len(nodes_by_type(graph, "fact")) == 2
    assert all(edge.type in {"supports", "relates"} for edge in graph.edges)


def test_graph_service_saves_graph(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    repo = GraphRepository(ws)
    graph = CaseGraphService(repo).build_and_save("case_001", [make_evidence("ev1")])
    saved = repo.get_json("case_001", "graph")
    assert saved["id"] == graph.id
    assert saved["nodes"]
