# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Append-only timeline repository."""

from __future__ import annotations

import json
from pathlib import Path

from _infra.feos.models import TimelineEvent
from _infra.feos.storage import FEOSWorkspace, FileLock


class TimelineRepository:
    def __init__(self, workspace: FEOSWorkspace):
        self.workspace = workspace

    def timeline_path(self, case_id: str) -> Path:
        return self.workspace.case_dir(case_id) / "timeline.jsonl"

    def append(self, event: TimelineEvent) -> Path:
        path = self.timeline_path(event.case_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(path.with_suffix(".lock")):
            with path.open("a", encoding="utf-8") as f:
                f.write(event.to_json_line() + "\n")
        return path

    def list(self, case_id: str) -> list[TimelineEvent]:
        path = self.timeline_path(case_id)
        if not path.exists():
            return []
        events = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(TimelineEvent(**json.loads(line)))
        return events
