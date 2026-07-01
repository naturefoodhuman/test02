# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import platform
import sys

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, safe_env_summary


class RuntimeCollector:
    collector_id = "runtime"
    required = False

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return True

    def collect(self, request: EvidenceCollectionRequest):
        raw = f"python={sys.version}\nplatform={platform.platform()}\nenv:\n{safe_env_summary()}"
        return [collected(self.collector_id, EvidenceType.RUNTIME_ENV, raw, origin="runtime_env")]
