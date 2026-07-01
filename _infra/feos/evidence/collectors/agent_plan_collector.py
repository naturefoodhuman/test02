# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected


class AgentPlanCollector:
    collector_id = "agent_plan"
    required = False

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return bool(request.agent_plan)

    def collect(self, request: EvidenceCollectionRequest):
        return [collected(self.collector_id, EvidenceType.AGENT_PROMPT, request.agent_plan or "", origin="agent_behavior")]
