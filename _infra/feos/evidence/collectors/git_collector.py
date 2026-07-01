# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.adapters import GitAdapter
from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected


class GitCollector:
    collector_id = "git"
    required = False

    def __init__(self, root: Path | None = None, adapter: GitAdapter | None = None):
        self.root = root or Path.cwd()
        self.adapter = adapter or GitAdapter(self.root)

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return True

    def collect(self, request: EvidenceCollectionRequest):
        raw = f"branch: {self.adapter.current_branch()}\ncommit: {self.adapter.current_commit()}\nstatus:\n{self.adapter.status()}"
        return [collected(self.collector_id, EvidenceType.RUNTIME_ENV, raw, origin="git")]
