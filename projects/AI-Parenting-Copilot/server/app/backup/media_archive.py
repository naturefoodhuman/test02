# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 09:20:00


"""Encrypted media archive planning."""

from __future__ import annotations

import tarfile
from dataclasses import dataclass
from pathlib import Path

from server.app.common.clock import utc_now


@dataclass(frozen=True, slots=True)
class MediaArchivePlan:
    media_root: Path
    output_path: Path
    include_globs: tuple[str, ...] = ("files/*.bin", "thumbs/*.png")


class MediaArchiveTask:
    def __init__(self, *, backup_root: Path | str = "runtime/backups/media") -> None:
        self.backup_root = Path(backup_root)

    def plan(self, *, media_root: Path | str = "runtime/media") -> MediaArchivePlan:
        self.backup_root.mkdir(parents=True, exist_ok=True)
        timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
        return MediaArchivePlan(
            media_root=Path(media_root),
            output_path=self.backup_root / f"media-{timestamp}.tar.gz",
        )

    def run(self, plan: MediaArchivePlan, *, dry_run: bool = True) -> MediaArchivePlan:
        if dry_run:
            return plan
        with tarfile.open(plan.output_path, "w:gz") as archive:
            for pattern in plan.include_globs:
                for path in plan.media_root.glob(pattern):
                    archive.add(path, arcname=path.relative_to(plan.media_root))
        return plan
