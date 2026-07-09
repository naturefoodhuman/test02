# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 09:20:00


"""PostgreSQL dump task planning and dry-run execution."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from server.app.common.clock import utc_now


@dataclass(frozen=True, slots=True)
class PGDumpPlan:
    database_url: str
    output_path: Path
    command: list[str]

    @property
    def shell_safe_command(self) -> str:
        return " ".join(shlex.quote(part) for part in self.command)


class PGDumpTask:
    def __init__(self, *, backup_root: Path | str = "runtime/backups/pg") -> None:
        self.backup_root = Path(backup_root)

    def plan(self, *, database_url: str, label: str = "parenting") -> PGDumpPlan:
        self.backup_root.mkdir(parents=True, exist_ok=True)
        timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
        output_path = self.backup_root / f"{label}-{timestamp}.dump"
        command = ["pg_dump", "--format=custom", "--file", str(output_path), database_url]
        return PGDumpPlan(database_url=database_url, output_path=output_path, command=command)

    def run(self, plan: PGDumpPlan, *, dry_run: bool = True) -> PGDumpPlan:
        if dry_run:
            return plan
        subprocess.check_call(plan.command)
        return plan
