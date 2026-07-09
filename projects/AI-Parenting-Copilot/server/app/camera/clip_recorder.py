# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:55:00


"""Clip recorder planning helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClipPlan:
    event_id: str
    pre_seconds: int = 15
    post_seconds: int = 30
    path: str | None = None


class ClipRecorder:
    def plan_clip(self, *, event_id: str, root: str = "runtime/media/clips") -> ClipPlan:
        return ClipPlan(event_id=event_id, path=f"{root}/{event_id}.mp4")
