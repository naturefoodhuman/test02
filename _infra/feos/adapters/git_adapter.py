# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Local git adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitAdapter:
    def __init__(self, root: Path):
        self.root = root

    def run(self, args: list[str]) -> str:
        try:
            return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.STDOUT)
        except Exception as exc:
            return f"git command failed: {exc}"

    def status(self) -> str:
        return self.run(["status", "--short"])

    def diff(self, paths: list[str] | None = None) -> str:
        return self.run(["diff", "--", *(paths or [])])

    def current_commit(self) -> str | None:
        out = self.run(["rev-parse", "HEAD"]).strip()
        return out if out and "failed" not in out else None

    def current_branch(self) -> str | None:
        out = self.run(["branch", "--show-current"]).strip()
        return out or None
