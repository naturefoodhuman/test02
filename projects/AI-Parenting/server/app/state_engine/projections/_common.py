# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""projection 共享工具（APC-T015）。

过滤软删除事件、按 event_type 筛选、24h 窗口判定。纯函数，无副作用。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from ...events.domain import ObservationEvent

# 24h 窗口（架构 §10.1 各指标均"近 24h"）。
WINDOW = timedelta(hours=24)


def active_events(events: Iterable[ObservationEvent], event_type: str) -> list[ObservationEvent]:
    """筛选未删除 + 指定 event_type 的事件（按 start_time 升序）。"""
    selected = [e for e in events if not e.is_deleted and e.event_type == event_type]
    selected.sort(key=lambda e: e.start_time)
    return selected


def in_window(event: ObservationEvent, now: datetime) -> bool:
    """事件 start_time 是否在 [now-24h, now] 窗口内。"""
    return event.start_time >= now - WINDOW and event.start_time <= now


def window_events(
    events: Iterable[ObservationEvent], event_type: str, now: datetime
) -> list[ObservationEvent]:
    """未删除 + 指定 event_type + 24h 窗口内事件（升序）。"""
    return [e for e in active_events(events, event_type) if in_window(e, now)]


def seconds_between(start: datetime, end: datetime) -> float:
    """两时间差秒数（end - start）。"""
    return (end - start).total_seconds()


__all__ = ["WINDOW", "active_events", "in_window", "seconds_between", "window_events"]
