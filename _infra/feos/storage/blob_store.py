# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Content-addressed blob storage helper."""

from __future__ import annotations

from pathlib import Path

from .atomic_writer import atomic_write_bytes
from .hashing import sha256_bytes


class BlobStore:
    def __init__(self, root: Path):
        self.root = root

    def put(self, data: bytes, suffix: str = ".bin") -> tuple[str, Path]:
        digest = sha256_bytes(data)
        hex_part = digest.split(":", 1)[1]
        path = self.root / hex_part[:2] / f"{hex_part}{suffix}"
        atomic_write_bytes(path, data)
        return digest, path
