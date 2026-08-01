# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 09:20:00


"""APC-T044 backup task tests."""

from __future__ import annotations

from pathlib import Path

from server.app.backup.media_archive import MediaArchiveTask
from server.app.backup.pg_dump_task import PGDumpTask
from server.app.backup.restore_drill import RestoreDrillPlanner


def test_pg_dump_plan_uses_custom_format_and_safe_output(tmp_path: Path) -> None:
    plan = PGDumpTask(backup_root=tmp_path).plan(database_url="postgresql://u:p@localhost/db")

    assert "pg_dump" in plan.command[0]
    assert "--format=custom" in plan.command
    assert plan.output_path.suffix == ".dump"
    assert "postgresql://u:p@localhost/db" in plan.shell_safe_command


def test_media_archive_plan_keeps_encrypted_files_only(tmp_path: Path) -> None:
    plan = MediaArchiveTask(backup_root=tmp_path).plan(media_root="runtime/media")

    assert "files/*.bin" in plan.include_globs
    assert "thumbs/*.png" in plan.include_globs
    assert plan.output_path.name.endswith(".tar.gz")


def test_restore_drill_plan_and_manifest(tmp_path: Path) -> None:
    planner = RestoreDrillPlanner(restore_root=tmp_path)
    plan = planner.plan(
        database_url="postgresql://u:p@localhost/restore",
        pg_dump_path="runtime/backups/pg/latest.dump",
        media_archive_path="runtime/backups/media/latest.tar.gz",
        clean_before_restore=True,
    )
    manifest = planner.manifest(
        pg_dump_path=plan.pg_dump_path,
        media_archive_path=plan.media_archive_path,
    )
    manifest_path = planner.write_manifest(manifest)

    assert "pg_restore" in plan.command[0]
    assert "--clean" in plan.command
    assert "latest.dump" in plan.shell_safe_command
    assert "pg_restore --list succeeds" in manifest.verification_steps
    assert manifest_path.exists()
    assert "latest.tar.gz" in manifest_path.read_text(encoding="utf-8")
