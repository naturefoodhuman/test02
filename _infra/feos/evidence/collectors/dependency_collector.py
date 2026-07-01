# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, read_text_limited


class DependencyCollector:
    collector_id = "dependency"
    required = False

    def __init__(self, root: Path | None = None):
        self.root = root or Path.cwd()

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return True

    def collect(self, request: EvidenceCollectionRequest):
        out = []
        for pattern in ["requirements*.txt", "pyproject.toml", "uv.lock", "poetry.lock", "package-lock.json"]:
            for path in self.root.glob(pattern):
                if path.is_file():
                    out.append(collected(self.collector_id, EvidenceType.DEPENDENCY_LOCK, read_text_limited(path, 65536), origin="dependency_file", metadata={"path": str(path.relative_to(self.root))}))
        return out
