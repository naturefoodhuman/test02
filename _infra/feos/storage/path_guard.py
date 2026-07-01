# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Path traversal guard for FEOS local storage."""

from __future__ import annotations

from pathlib import Path

from _infra.feos.errors import FEOSStorageError


class PathGuard:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def resolve(self, relative: str | Path) -> Path:
        candidate = Path(relative)
        if candidate.is_absolute():
            raise FEOSStorageError(f"absolute paths are not allowed: {relative}")
        resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise FEOSStorageError(f"path escapes FEOS workspace: {relative}") from exc
        return resolved
