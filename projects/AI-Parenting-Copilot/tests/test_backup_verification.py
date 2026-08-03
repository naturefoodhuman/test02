# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 23:35:00

"""Backup manifest verifier tests."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from server.app.backup.verification import BackupManifestVerifier


def test_backup_manifest_verifier_accepts_dry_run_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "created_at": "2026-08-03T00:00:00Z",
                "pg_dump_path": "runtime/backups/pg/latest.dump",
                "media_archive_path": "runtime/backups/media/latest.tar.gz",
            }
        ),
        encoding="utf-8",
    )

    result = BackupManifestVerifier(project_root=Path(".")).verify_manifest_file(manifest)

    assert result.ok is True
    assert result.checks["pg_dump_extension"] == "ok"
    assert result.checks["media_archive_extension"] == "ok"
    assert any(command.startswith("pg_restore --list") for command in result.next_commands)
    assert any(command.startswith("tar -tzf") for command in result.next_commands)


def test_backup_manifest_verifier_reads_safe_media_archive(tmp_path: Path) -> None:
    media = tmp_path / "media.tar.gz"
    source_root = tmp_path / "source"
    (source_root / "files").mkdir(parents=True)
    (source_root / "thumbs").mkdir()
    (source_root / "files" / "a.bin").write_bytes(b"encrypted")
    (source_root / "thumbs" / "a.png").write_bytes(b"png")
    with tarfile.open(media, "w:gz") as archive:
        archive.add(source_root / "files" / "a.bin", arcname="files/a.bin")
        archive.add(source_root / "thumbs" / "a.png", arcname="thumbs/a.png")
    dump = tmp_path / "latest.dump"
    dump.write_bytes(b"not-a-real-dump-but-present")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "created_at": "2026-08-03T00:00:00Z",
                "pg_dump_path": str(dump),
                "media_archive_path": str(media),
            }
        ),
        encoding="utf-8",
    )

    result = BackupManifestVerifier().verify_manifest_file(manifest, require_files=True)

    assert result.ok is True
    assert result.checks["media_archive_readable"] == "ok"
    assert result.checks["media_archive_paths_safe"] == "ok"
    assert result.checks["media_archive_scope"] == "ok"


def test_backup_manifest_verifier_rejects_unsafe_media_archive(tmp_path: Path) -> None:
    media = tmp_path / "media.tar.gz"
    source = tmp_path / "secret.txt"
    source.write_text("secret", encoding="utf-8")
    with tarfile.open(media, "w:gz") as archive:
        archive.add(source, arcname="../secret.txt")
    dump = tmp_path / "latest.dump"
    dump.write_bytes(b"dump")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "created_at": "2026-08-03T00:00:00Z",
                "pg_dump_path": str(dump),
                "media_archive_path": str(media),
            }
        ),
        encoding="utf-8",
    )

    result = BackupManifestVerifier().verify_manifest_file(manifest, require_files=True)

    assert result.ok is False
    assert result.checks["media_archive_paths_safe"] == "failed"
    assert any("unsafe paths" in error for error in result.errors)
