# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.evidence import CollectorRegistry, EvidenceService
from _infra.feos.ports.collectors import CollectedEvidence, EvidenceCollectionRequest
from _infra.feos.repositories import TimelineRepository
from _infra.feos.storage import FEOSWorkspace, read_yaml, sha256_text


class UserCollector:
    collector_id = "user_input"
    required = True

    def can_collect(self, request):
        return bool(request.user_input)

    def collect(self, request):
        return [CollectedEvidence(collector_id=self.collector_id, evidence_type="user_input", raw_content=request.user_input, required=True)]


class OptionalFailingCollector:
    collector_id = "optional_fail"
    required = False

    def can_collect(self, request):
        return True

    def collect(self, request):
        raise RuntimeError("boom")


class RequiredFailingCollector(OptionalFailingCollector):
    collector_id = "required_fail"
    required = True


def test_evidence_service_saves_raw_normalized_index_and_timeline(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    reg = CollectorRegistry()
    reg.register(UserCollector())
    service = EvidenceService(ws, reg, TimelineRepository(ws))
    result = service.collect(EvidenceCollectionRequest(case_id="case_001", user_input="hello evidence"))
    assert result.ok is True
    ev = result.evidence[0]
    raw_path = ws.root / ev.content.raw_ref
    assert raw_path.read_text() == "hello evidence"
    assert ev.metadata["hash"] == sha256_text("hello evidence")
    assert (ws.root / "cases" / "case_001" / "evidence" / "normalized" / f"{ev.id}.yaml").exists()
    index = read_yaml(ws.root / "cases" / "case_001" / "evidence" / "index.yaml")
    assert ev.id in index["evidence_ids"]
    assert TimelineRepository(ws).list("case_001")[0].type == "evidence_collected"


def test_optional_failure_warns_required_failure_errors(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    reg = CollectorRegistry(); reg.register(OptionalFailingCollector())
    result = EvidenceService(ws, reg).collect(EvidenceCollectionRequest(case_id="case_001"))
    assert result.ok is True
    assert result.warnings

    reg2 = CollectorRegistry(); reg2.register(RequiredFailingCollector())
    result2 = EvidenceService(ws, reg2).collect(EvidenceCollectionRequest(case_id="case_002"))
    assert result2.ok is False
    assert result2.errors
