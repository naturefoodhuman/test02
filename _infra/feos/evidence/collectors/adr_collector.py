# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, read_text_limited


class ADRCollector:
    collector_id = "adr"
    required = False

    def __init__(self, root: Path | None = None):
        self.root = root or Path.cwd()

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return (self.root / "docs" / "adr").exists()

    def collect(self, request: EvidenceCollectionRequest):
        out = []
        for path in sorted((self.root / "docs" / "adr").glob("ADR-*.md")):
            out.append(collected(self.collector_id, EvidenceType.ARCHITECTURE_DOC, read_text_limited(path, 32768), origin="adr", metadata={"path": str(path.relative_to(self.root))}))
        return out
