# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.detector import DetectorSignals
from _infra.feos.errors import FEOSError
from _infra.feos.evidence import CollectorRegistry
from _infra.feos.ports.collectors import CollectedEvidence, EvidenceCollectionRequest


class DummyCollector:
    collector_id = "dummy"
    required = False

    def can_collect(self, request):
        return True

    def collect(self, request):
        return [CollectedEvidence(collector_id=self.collector_id, evidence_type="user_input", raw_content="hello")]


class FailingCollector(DummyCollector):
    collector_id = "failing"

    def collect(self, request):
        raise RuntimeError("boom")


def test_registry_register_select_and_duplicate():
    reg = CollectorRegistry()
    reg.register(DummyCollector())
    selected = reg.enabled_collectors(EvidenceCollectionRequest(case_id="case_001"))
    assert selected[0].collector_id == "dummy"
    with pytest.raises(FEOSError):
        reg.register(DummyCollector())
