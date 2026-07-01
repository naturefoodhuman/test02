# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import os
from pathlib import Path

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import CollectedEvidence

SECRET_KEYS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "COOKIE", "AUTH")


def collected(collector_id: str, evidence_type: EvidenceType | str, raw: str, origin: str = "collector", subtype: str | None = None, metadata: dict | None = None, required: bool = False) -> CollectedEvidence:
    return CollectedEvidence(collector_id=collector_id, evidence_type=evidence_type, raw_content=raw, origin=origin, subtype=subtype, metadata=metadata or {}, required=required)


def safe_env_summary() -> str:
    lines = []
    for key, value in sorted(os.environ.items()):
        if any(secret in key.upper() for secret in SECRET_KEYS):
            lines.append(f"{key}=<redacted>")
        elif key.startswith(("FEOS_", "FORGE_", "PYTHON", "VIRTUAL_ENV", "PATH")):
            lines.append(f"{key}={value[:200]}")
    return "\n".join(lines)


def read_text_limited(path: Path, max_bytes: int = 65536) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def is_denied(path: str, deny_files: list[str]) -> bool:
    name = Path(path).name
    if name in {".env", "cookies", "cookies.txt"}:
        return True
    return any(Path(path).match(pattern) or name == pattern for pattern in deny_files)
