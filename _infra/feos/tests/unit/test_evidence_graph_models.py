# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest
from pydantic import ValidationError

from _infra.feos.models import (
    CaseGraph,
    Evidence,
    EvidenceContent,
    EvidenceSource,
    GraphEdge,
    GraphNode,
    Hypothesis,
)


def test_evidence_yaml_round_trip():
    ev = Evidence(
        id="ev_stacktrace_001",
        case_id="case_001",
        type="stack_trace",
        source=EvidenceSource(collector="StackTraceCollector", origin="runtime_log"),
        content=EvidenceContent(raw_ref="evidence/raw/ev_stacktrace_001.txt", normalized={"error": "ValidationError"}),
    )
    loaded = Evidence.from_yaml_text(ev.to_yaml_text())
    assert loaded.content.raw_ref == "evidence/raw/ev_stacktrace_001.txt"
    assert loaded.content.normalized["error"] == "ValidationError"


def test_graph_json_round_trip_and_confidence_range():
    graph = CaseGraph(
        id="graph_001",
        case_id="case_001",
        nodes=[GraphNode(id="ev1", type="evidence", label="stacktrace")],
        edges=[GraphEdge(source="ev1", target="hyp1", type="supports", confidence=0.8)],
    )
    loaded = CaseGraph.model_validate_json(graph.model_dump_json())
    assert loaded.edges[0].confidence == 0.8
    with pytest.raises(ValidationError):
        GraphEdge(source="a", target="b", type="supports", confidence=1.5)


def test_hypothesis_evidence_refs():
    hyp = Hypothesis(id="hyp_001", case_id="case_001", statement="schema mismatch", supports=["ev1"], refutes=["ev2"])
    assert hyp.status == "Proposed"
    assert hyp.supports == ["ev1"]
    assert hyp.refutes == ["ev2"]
