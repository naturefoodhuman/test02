# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:25:00

"""Restore drill planning for PostgreSQL dumps and media archives."""

from __future__ import annotations

import json
import shlex
from dataclasses import asdict, dataclass, field
from pathlib import Path

from server.app.common.clock import utc_now


@dataclass(frozen=True, slots=True)
class RestorePlan:
    database_url: str
    pg_dump_path: Path
    command: list[str]
    media_archive_path: Path | None = None

    @property
    def shell_safe_command(self) -> str:
        return " ".join(shlex.quote(part) for part in self.command)


@dataclass(frozen=True, slots=True)
class BackupManifest:
    created_at: str
    pg_dump_path: str | None = None
    media_archive_path: str | None = None
    verification_steps: tuple[str, ...] = field(
        default_factory=lambda: (
            "pg_restore --list succeeds",
            "restore target database is disposable",
            "application can run db-current after restore",
            "media archive extracts under an empty target directory",
        )
    )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class RestoreDrillPlanner:
    def __init__(self, *, restore_root: Path | str = "runtime/restore-drills") -> None:
        self.restore_root = Path(restore_root)

    def plan(
        self,
        *,
        database_url: str,
        pg_dump_path: Path | str,
        media_archive_path: Path | str | None = None,
        clean_before_restore: bool = False,
    ) -> RestorePlan:
        self.restore_root.mkdir(parents=True, exist_ok=True)
        command = ["pg_restore", "--dbname", database_url]
        if clean_before_restore:
            command.append("--clean")
        command.append(str(pg_dump_path))
        return RestorePlan(
            database_url=database_url,
            pg_dump_path=Path(pg_dump_path),
            media_archive_path=Path(media_archive_path) if media_archive_path else None,
            command=command,
        )

    def manifest(
        self,
        *,
        pg_dump_path: Path | str | None = None,
        media_archive_path: Path | str | None = None,
    ) -> BackupManifest:
        return BackupManifest(
            created_at=utc_now().isoformat(),
            pg_dump_path=str(pg_dump_path) if pg_dump_path else None,
            media_archive_path=str(media_archive_path) if media_archive_path else None,
        )

    def write_manifest(self, manifest: BackupManifest) -> Path:
        self.restore_root.mkdir(parents=True, exist_ok=True)
        path = self.restore_root / f"backup-manifest-{utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
        path.write_text(manifest.to_json(), encoding="utf-8")
        return path
