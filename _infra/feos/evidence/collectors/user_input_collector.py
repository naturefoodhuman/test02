# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected


class UserInputCollector:
    collector_id = "user_input"
    required = True

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return bool(request.user_input)

    def collect(self, request: EvidenceCollectionRequest):
        return [collected(self.collector_id, EvidenceType.USER_INPUT, request.user_input or "", origin="user_input", required=True)]
