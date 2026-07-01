# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, is_denied, read_text_limited


class ConfigCollector:
    collector_id = "config"
    required = False

    def __init__(self, root: Path | None = None, allow_files: list[str] | None = None, deny_files: list[str] | None = None):
        self.root = root or Path.cwd()
        self.allow_files = allow_files or ["config/*.yaml", "pyproject.toml", "requirements*.txt", "Makefile"]
        self.deny_files = deny_files or [".env", "_infra/.env", "*.key", "*.pem"]

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return True

    def collect(self, request: EvidenceCollectionRequest):
        out = []
        for pattern in self.allow_files:
            for path in self.root.glob(pattern):
                rel = str(path.relative_to(self.root))
                if path.is_file() and not is_denied(rel, self.deny_files):
                    out.append(collected(self.collector_id, EvidenceType.CONFIG, read_text_limited(path, 32768), origin="config_file", metadata={"path": rel}))
        return out
