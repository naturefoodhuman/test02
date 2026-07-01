# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Generic FEOS artifact repository.

This is the shared implementation behind FEOS-011 repository wrappers. It is
intentionally storage-only and contains no business judgment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _infra.feos.storage import FEOSWorkspace, atomic_write_bytes, read_json, read_yaml, sha256_bytes, write_json, write_yaml


@dataclass
class RawArtifactResult:
    ref: str
    path: Path
    hash: str


class ArtifactRepository:
    def __init__(self, workspace: FEOSWorkspace, subdir: str, extension: str = ".yaml"):
        self.workspace = workspace
        self.subdir = subdir.strip("/")
        self.extension = extension

    def dir(self, case_id: str) -> Path:
        return self.workspace.case_dir(case_id) / self.subdir

    def path(self, case_id: str, artifact_id: str, extension: str | None = None) -> Path:
        ext = extension if extension is not None else self.extension
        if "/" in artifact_id or ".." in artifact_id:
            raise ValueError(f"invalid artifact id: {artifact_id}")
        return self.dir(case_id) / f"{artifact_id}{ext}"

    def put_yaml(self, case_id: str, artifact_id: str, data: Any) -> Path:
        path = self.path(case_id, artifact_id, ".yaml")
        write_yaml(path, data)
        return path

    def get_yaml(self, case_id: str, artifact_id: str) -> Any:
        return read_yaml(self.path(case_id, artifact_id, ".yaml"))

    def put_json(self, case_id: str, artifact_id: str, data: Any) -> Path:
        path = self.path(case_id, artifact_id, ".json")
        write_json(path, data)
        return path

    def get_json(self, case_id: str, artifact_id: str) -> Any:
        return read_json(self.path(case_id, artifact_id, ".json"))

    def put_text(self, case_id: str, artifact_id: str, text: str, extension: str = ".md") -> Path:
        path = self.path(case_id, artifact_id, extension)
        atomic_write_bytes(path, text.encode("utf-8"))
        return path

    def put_raw(self, case_id: str, artifact_id: str, data: bytes, extension: str = ".bin") -> RawArtifactResult:
        path = self.path(case_id, artifact_id, extension)
        digest = sha256_bytes(data)
        atomic_write_bytes(path, data)
        return RawArtifactResult(ref=str(path.relative_to(self.workspace.root)), path=path, hash=digest)

    def list_paths(self, case_id: str) -> list[Path]:
        root = self.dir(case_id)
        if not root.exists():
            return []
        return sorted(p for p in root.rglob("*") if p.is_file())
