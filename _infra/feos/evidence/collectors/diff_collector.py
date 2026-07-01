# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.adapters import GitAdapter
from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected


class DiffCollector:
    collector_id = "diff"
    required = False

    def __init__(self, root: Path | None = None, adapter: GitAdapter | None = None, max_bytes: int = 262144):
        self.root = root or Path.cwd()
        self.adapter = adapter or GitAdapter(self.root)
        self.max_bytes = max_bytes

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return True

    def collect(self, request: EvidenceCollectionRequest):
        diff = self.adapter.diff(request.paths)[: self.max_bytes]
        return [collected(self.collector_id, EvidenceType.GIT_DIFF, diff, origin="git_diff", subtype="truncated" if len(diff) >= self.max_bytes else None)]
