# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 23:35:00

"""Backup manifest and archive verification helpers.

These checks are safe to run without a real NAS or disposable PostgreSQL restore DB.
They validate the restore-drill artifacts and produce explicit commands for the
remaining local-only verification steps.
"""

from __future__ import annotations

import json
import shlex
import tarfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BackupVerificationResult:
    ok: bool
    checks: dict[str, str]
    errors: tuple[str, ...] = field(default_factory=tuple)
    next_commands: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class BackupManifestVerifier:
    def __init__(self, *, project_root: Path | str = ".") -> None:
        self.project_root = Path(project_root)

    def verify_manifest_file(
        self,
        manifest_path: Path | str,
        *,
        require_files: bool = False,
        restore_database_url: str = "postgresql://parenting:parenting@127.0.0.1:5432/parenting_restore",
    ) -> BackupVerificationResult:
        path = self._resolve(manifest_path)
        errors: list[str] = []
        checks: dict[str, str] = {}
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return BackupVerificationResult(
                ok=False,
                checks={"manifest_json": "failed"},
                errors=(f"manifest could not be read: {exc}",),
            )
        checks["manifest_json"] = "ok"
        pg_dump_path = self._optional_path(manifest.get("pg_dump_path"))
        media_archive_path = self._optional_path(manifest.get("media_archive_path"))
        if pg_dump_path is None:
            errors.append("manifest missing pg_dump_path")
            checks["pg_dump_path"] = "missing"
        else:
            self._verify_pg_dump_path(pg_dump_path, require_files, checks, errors)
        if media_archive_path is None:
            checks["media_archive_path"] = "not_declared"
        else:
            self._verify_media_archive(media_archive_path, require_files, checks, errors)
        next_commands = self._next_commands(pg_dump_path, media_archive_path, restore_database_url)
        return BackupVerificationResult(
            ok=not errors,
            checks=checks,
            errors=tuple(errors),
            next_commands=next_commands,
        )

    def _resolve(self, path: Path | str) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.project_root / candidate

    def _optional_path(self, value: object) -> Path | None:
        if value is None or str(value) == "":
            return None
        return self._resolve(str(value))

    @staticmethod
    def _verify_pg_dump_path(
        path: Path,
        require_files: bool,
        checks: dict[str, str],
        errors: list[str],
    ) -> None:
        if path.suffix != ".dump":
            errors.append(f"pg_dump_path must end with .dump: {path}")
            checks["pg_dump_extension"] = "failed"
        else:
            checks["pg_dump_extension"] = "ok"
        if require_files and not path.exists():
            errors.append(f"pg_dump_path does not exist: {path}")
            checks["pg_dump_exists"] = "missing"
        elif path.exists():
            checks["pg_dump_exists"] = "ok"
        else:
            checks["pg_dump_exists"] = "not_required"

    @staticmethod
    def _verify_media_archive(
        path: Path,
        require_files: bool,
        checks: dict[str, str],
        errors: list[str],
    ) -> None:
        if not str(path).endswith(".tar.gz"):
            errors.append(f"media_archive_path must end with .tar.gz: {path}")
            checks["media_archive_extension"] = "failed"
        else:
            checks["media_archive_extension"] = "ok"
        if not path.exists():
            if require_files:
                errors.append(f"media_archive_path does not exist: {path}")
                checks["media_archive_exists"] = "missing"
            else:
                checks["media_archive_exists"] = "not_required"
            return
        checks["media_archive_exists"] = "ok"
        try:
            with tarfile.open(path, "r:gz") as archive:
                members = archive.getnames()
        except Exception as exc:
            errors.append(f"media archive cannot be read: {exc}")
            checks["media_archive_readable"] = "failed"
            return
        checks["media_archive_readable"] = "ok"
        unsafe = [
            member for member in members if member.startswith("/") or ".." in Path(member).parts
        ]
        if unsafe:
            errors.append(f"media archive contains unsafe paths: {unsafe}")
            checks["media_archive_paths_safe"] = "failed"
        else:
            checks["media_archive_paths_safe"] = "ok"
        disallowed = [
            member
            for member in members
            if not (member.startswith("files/") or member.startswith("thumbs/"))
        ]
        if disallowed:
            errors.append(f"media archive contains disallowed members: {disallowed}")
            checks["media_archive_scope"] = "failed"
        else:
            checks["media_archive_scope"] = "ok"

    @staticmethod
    def _next_commands(
        pg_dump_path: Path | None,
        media_archive_path: Path | None,
        restore_database_url: str,
    ) -> tuple[str, ...]:
        commands: list[str] = []
        if pg_dump_path is not None:
            commands.append(" ".join(["pg_restore", "--list", shlex.quote(str(pg_dump_path))]))
            commands.append(
                " ".join(
                    [
                        "pg_restore",
                        "--dbname",
                        shlex.quote(restore_database_url),
                        "--clean",
                        shlex.quote(str(pg_dump_path)),
                    ]
                )
            )
        if media_archive_path is not None:
            commands.append(
                " ".join(
                    [
                        "tar",
                        "-tzf",
                        shlex.quote(str(media_archive_path)),
                    ]
                )
            )
        return tuple(commands)
