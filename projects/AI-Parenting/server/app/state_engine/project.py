# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/project.py —— P0 projection 聚合入口（APC-T015）。
# 依据：ENGINEERING_DESIGN §2 M06、§3 state_engine；ARCHITECTURE_FINAL §10.1、§6.3；
#       TASK_BACKLOG APC-T015（给定 fixture 事件集输出稳定 DerivedBabyState）。
# 设计：project_state(events, now) 聚合 5 个 P0 projection → DerivedBabyState。
#       纯函数，不写 DB（upsert 在 T016）。source_event_range 取所有未删除事件最早/最晚 start_time。
# 边界：只派生不告警；不做医疗判断。

"""P0 projection 聚合入口（APC-T015）。

纯函数：``project_state(events, now)`` 聚合 feeding/diaper/sleep/temperature/supplement
五个 P0 projection，输出 ``DerivedBabyState`` 快照。``source_event_range`` 取所有未删除
事件最早/最晚 start_time（架构 §6.3 snapshot 含 source event range，便于审计追溯）。

T015 只做 projection，不写 DB（``derived_baby_state`` upsert 在 APC-T016）。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ..events.domain import ObservationEvent
from .domain import DerivedBabyState
from .projections import (
    project_diaper,
    project_feeding,
    project_sleep,
    project_supplement,
    project_temperature,
)


def project_state(
    events: Iterable[ObservationEvent], now: datetime
) -> DerivedBabyState:
    """聚合 P0 projection → DerivedBabyState（纯函数，APC-T015）。

    Args:
        events: 该 baby 的 ObservationEvent 集合（含软删除，projection 内部过滤）。
        now: 参考时间（快照 computed_at + 24h 窗口右端）。

    Returns:
        ``DerivedBabyState`` 快照（feeding/diaper/sleep/temperature/supplement 指标）。
    """
    event_list = list(events)
    active = [e for e in event_list if not e.is_deleted]
    if active:
        starts = [e.start_time for e in active]
        source_range: tuple[datetime | None, datetime | None] = (min(starts), max(starts))
    else:
        source_range = (None, None)

    return DerivedBabyState(
        feeding=project_feeding(event_list, now),
        diaper=project_diaper(event_list, now),
        sleep=project_sleep(event_list, now),
        temperature=project_temperature(event_list, now),
        supplement=project_supplement(event_list, now),
        computed_at=now,
        source_event_range=source_range,
    )


__all__ = ["project_state"]
