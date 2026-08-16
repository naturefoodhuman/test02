# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/projections/supplement.py —— 补剂派生指标（APC-T015）。
# 依据：ARCHITECTURE_FINAL §10.1（补剂，§7.1 supplement parser）；TASK_BACKLOG APC-T015。
# 设计：纯函数，输入未删除 supplement 事件 + now，输出 SupplementProjection。
#       last_supplement_ago_seconds：最近 supplement 事件 start_time 距 now。
#       last_supplement_name：normalized_payload.name。
# 边界：只计算不告警。

"""补剂派生指标（APC-T015）。

纯函数：输入未删除 ``supplement`` 事件集合 + 参考时间 ``now``，输出 ``SupplementProjection``：
    - ``last_supplement_ago_seconds``：距上次补剂秒数（无记录 None）。
    - ``last_supplement_name``：上次补剂名称（normalized_payload.name；无记录 None）。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ...events.domain import ObservationEvent
from ..domain import SupplementProjection
from ._common import active_events, seconds_between


def project_supplement(events: Iterable[ObservationEvent], now: datetime) -> SupplementProjection:
    """计算补剂派生指标（P0，纯函数）。"""
    active = active_events(events, "supplement")
    if not active:
        return SupplementProjection(last_supplement_ago_seconds=None, last_supplement_name=None)
    last = active[-1]
    name = last.normalized_payload.get("name")
    name_str = str(name) if name is not None else None
    return SupplementProjection(
        last_supplement_ago_seconds=seconds_between(last.start_time, now),
        last_supplement_name=name_str,
    )


__all__ = ["project_supplement"]
