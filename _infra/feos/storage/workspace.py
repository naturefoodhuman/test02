# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS workspace directory management."""

from __future__ import annotations

from pathlib import Path

from _infra.feos.config_loader import bootstrap_feos

from .path_guard import PathGuard


class FEOSWorkspace:
    REQUIRED_DIRS = [
        "cases",
        "policies",
        "renderer_profiles",
        "knowledge_index",
        "metrics",
        "cache",
    ]

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.guard = PathGuard(self.root)

    @classmethod
    def from_project(cls, project_root: Path | None = None) -> "FEOSWorkspace":
        context = bootstrap_feos(project_root=project_root)
        return cls(context.feos_home)

    def ensure_initialized(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for item in self.REQUIRED_DIRS:
            (self.root / item).mkdir(parents=True, exist_ok=True, mode=0o700)

    def case_dir(self, case_id: str) -> Path:
        if "/" in case_id or ".." in case_id or case_id.startswith("."):
            raise ValueError(f"invalid case id: {case_id}")
        return self.guard.resolve(Path("cases") / case_id)

    def resolve(self, relative: str | Path) -> Path:
        return self.guard.resolve(relative)
