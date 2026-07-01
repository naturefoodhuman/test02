# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Atomic file write helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class AtomicWriter:
    def write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        except Exception:
            try:
                tmp_path.unlink(missing_ok=True)
            finally:
                raise

    def write_text(self, path: Path, text: str, encoding: str = "utf-8") -> None:
        self.write_bytes(path, text.encode(encoding))


def atomic_write_bytes(path: Path, data: bytes) -> None:
    AtomicWriter().write_bytes(path, data)


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    AtomicWriter().write_text(path, text, encoding=encoding)
