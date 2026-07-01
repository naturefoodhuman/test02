# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import CaseProblem, EscalationCase
from _infra.feos.repositories import ArtifactRepository
from _infra.feos.retrieval import LexicalRetriever, SimilarityRetrievalService
from _infra.feos.storage import FEOSWorkspace, read_yaml


def test_lexical_retrieval_sorts_by_score():
    cases = [
        EscalationCase(id="case_1", title="schema validation error", problem=CaseProblem(user_goal="fix mcp schema")),
        EscalationCase(id="case_2", title="unrelated ui bug", problem=CaseProblem(user_goal="fix css")),
    ]
    results = LexicalRetriever().search("mcp schema validation", cases)
    assert results[0].case_id == "case_1"
    assert results[0].score > 0


def test_similarity_service_saves_results(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    repo = ArtifactRepository(ws, "retrieval")
    case = EscalationCase(id="case_old", title="tool call schema", problem=CaseProblem(user_goal="fix schema"))
    results = SimilarityRetrievalService(repo).search("schema", [case], case_id="case_new")
    assert results
    saved = read_yaml(ws.root / "cases" / "case_new" / "retrieval" / "similar_cases.yaml")
    assert saved["results"][0]["case_id"] == "case_old"
