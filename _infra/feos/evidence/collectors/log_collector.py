# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, read_text_limited


class LogCollector:
    collector_id = "log"
    required = False

    def __init__(self, root: Path | None = None, max_bytes: int = 65536):
        self.root = root or Path.cwd()
        self.max_bytes = max_bytes

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return bool(request.logs)

    def collect(self, request: EvidenceCollectionRequest):
        out = []
        for log in request.logs:
            path = (self.root / log).resolve() if not Path(log).is_absolute() else Path(log)
            if path.is_file():
                out.append(collected(self.collector_id, EvidenceType.LOG, read_text_limited(path, self.max_bytes), origin="log_file", metadata={"path": log}))
        return out
