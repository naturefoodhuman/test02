# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/projections/sleep.py —— 睡眠派生指标（APC-T015）。
# 依据：ARCHITECTURE_FINAL §10.1（24h 睡眠、当前会话）；TASK_BACKLOG APC-T015。
# 设计：纯函数，输入未删除 sleep 事件 + now，输出 SleepProjection。
#       total_seconds_24h：各 sleep 事件 [start,end] 与 [now-24h, now] 窗口交集之和；
#       未结束事件 end 取 now。current_session_started_at：未结束 sleep 事件的 start_time。
# 边界：只计算不告警。

"""睡眠派生指标（APC-T015）。

纯函数：输入未删除 ``sleep`` 事件集合 + 参考时间 ``now``，输出 ``SleepProjection``：
    - ``total_seconds_24h``：近 24h 睡眠总秒数（各事件 [start,end] 与窗口 [now-24h, now]
      交集之和；未结束事件 end 取 now）。
    - ``current_session_started_at``：当前进行中会话 start_time（未结束 sleep 事件）；
      无进行中会话为 None。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ...events.domain import ObservationEvent
from ..domain import SleepProjection
from ._common import WINDOW, active_events


def _overlap_seconds(
    start: datetime, end: datetime, win_start: datetime, win_end: datetime
) -> float:
    """[start,end] 与 [win_start,win_end] 交集秒数。"""
    lo = max(start, win_start)
    hi = min(end, win_end)
    if hi <= lo:
        return 0.0
    return (hi - lo).total_seconds()


def project_sleep(events: Iterable[ObservationEvent], now: datetime) -> SleepProjection:
    """计算睡眠派生指标（P0，纯函数）。"""
    active = active_events(events, "sleep")
    win_start = now - WINDOW
    total = 0.0
    current: datetime | None = None
    for e in active:
        end = e.end_time if e.end_time is not None else now
        # 进行中会话：未结束且 start <= now。
        if e.end_time is None and e.start_time <= now:
            current = e.start_time
        # 只累加与窗口有交集的事件（含 start 早于窗口但 end 在窗口内的长睡眠）。
        if e.start_time <= now and end >= win_start:
            total += _overlap_seconds(e.start_time, end, win_start, now)
    return SleepProjection(total_seconds_24h=total, current_session_started_at=current)


__all__ = ["project_sleep"]
