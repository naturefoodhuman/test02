# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.distillation import KnowledgeCandidateExtractor, KnowledgeDistillationService, KnowledgeWriter
from _infra.feos.models import CaseProblem, EscalationCase, Outcome
from _infra.feos.repositories import KnowledgeRepository
from _infra.feos.storage import FEOSWorkspace, read_yaml


def test_knowledge_candidate_and_writer(tmp_path):
    case = EscalationCase(id="case", title="T", problem=CaseProblem(user_goal="debug"))
    outcome = Outcome(id="out", case_id="case", status="resolved", summary="fixed")
    candidate = KnowledgeCandidateExtractor().extract(case, outcome, ["ev1"])
    assert candidate.status == "captured"
    assert "ev1" in candidate.source_refs
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    service = KnowledgeDistillationService(KnowledgeWriter(KnowledgeRepository(ws)))
    service.distill(case, outcome, ["ev1"])
    assert read_yaml(ws.root / "cases" / "case" / "knowledge" / "distilled.yaml")["knowledge"]
