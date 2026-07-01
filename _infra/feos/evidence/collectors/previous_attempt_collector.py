# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected


class PreviousAttemptCollector:
    collector_id = "previous_attempt"
    required = False

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return bool(request.previous_attempts)

    def collect(self, request: EvidenceCollectionRequest):
        return [collected(self.collector_id, EvidenceType.PREVIOUS_ATTEMPT, text, origin="previous_attempt", metadata={"index": i}) for i, text in enumerate(request.previous_attempts)]
