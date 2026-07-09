# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 09:20:00


"""APC-T044 backup task tests."""

from __future__ import annotations

from pathlib import Path

from server.app.backup.media_archive import MediaArchiveTask
from server.app.backup.pg_dump_task import PGDumpTask


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
