# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.errors import FEOSError
from _infra.feos.hypothesis import HypothesisManager, compute_confidence
from _infra.feos.models import CaseGraph
from _infra.feos.repositories import ArtifactRepository
from _infra.feos.storage import FEOSWorkspace, read_yaml


def test_confidence_and_graph_sync(tmp_path):
    assert compute_confidence(2, 1) == 2 / 3
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    manager = HypothesisManager(ArtifactRepository(ws, "hypothesis"))
    hyp = manager.create("case_001", "schema mismatch", supports=["ev1"], refutes=[])
    graph = manager.sync_graph(CaseGraph(id="graph_001", case_id="case_001"), hyp)
    assert graph.nodes[0].type == "hypothesis"
    assert graph.edges[0].type == "supports"
    manager.save_all("case_001", [hyp])
    saved = read_yaml(ws.root / "cases" / "case_001" / "hypothesis" / "hypotheses.yaml")
    assert saved["hypotheses"][0]["id"] == hyp.id


def test_hypothesis_not_fact():
    with pytest.raises(FEOSError):
        HypothesisManager().create("case_001", "Fact: this is not a hypothesis")
