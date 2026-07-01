# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, read_text_limited


class ArchitectureCollector:
    collector_id = "architecture"
    required = False

    def __init__(self, root: Path | None = None):
        self.root = root or Path.cwd()

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return True

    def collect(self, request: EvidenceCollectionRequest):
        out = []
        for name in ["FEOS_ARCHITECTURE_FINAL.md", "FEOS_ENGINEERING_DESIGN.md", "NETWORK_ARCHITECTURE_FINAL.md", "NETWORK_ENGINEERING_DESIGN.md", "PROJECT_DOSSIER_V4.md"]:
            path = self.root / name
            if path.is_file():
                out.append(collected(self.collector_id, EvidenceType.ARCHITECTURE_DOC, read_text_limited(path, 65536), origin="architecture_doc", metadata={"path": name}))
        return out
