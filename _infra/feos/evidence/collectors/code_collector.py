# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from ._helpers import collected, is_denied, read_text_limited


class CodeCollector:
    collector_id = "code"
    required = False

    def __init__(self, root: Path | None = None, deny_files: list[str] | None = None):
        self.root = root or Path.cwd()
        self.deny_files = deny_files or [".env", "*.key", "*.pem", "cookies*"]

    def can_collect(self, request: EvidenceCollectionRequest) -> bool:
        return bool(request.paths)

    def collect(self, request: EvidenceCollectionRequest):
        out = []
        for item in request.paths:
            if is_denied(item, self.deny_files):
                continue
            path = (self.root / item).resolve()
            if not str(path).startswith(str(self.root.resolve())) or not path.is_file():
                continue
            out.append(collected(self.collector_id, EvidenceType.CODE, read_text_limited(path), origin="code", metadata={"path": item}))
        return out
