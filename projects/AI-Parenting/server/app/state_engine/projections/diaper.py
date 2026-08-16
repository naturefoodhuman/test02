# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/projections/diaper.py —— 尿布派生指标（APC-T015）。
# 依据：ARCHITECTURE_FINAL §10.1（湿/脏尿布数）；TASK_BACKLOG APC-T015。
# 设计：纯函数，输入未删除 diaper 事件 + now，输出 DiaperProjection。
#       type 取 normalized_payload.type（wet/dirty/mixed）；mixed 同时计入湿与脏。
# 边界：只计算不告警。

"""尿布派生指标（APC-T015）。

纯函数：输入未删除 ``diaper`` 事件集合 + 参考时间 ``now``，输出 ``DiaperProjection``：
    - ``wet_count_24h`` / ``dirty_count_24h``：近 24h 湿/脏尿布次数。
      type=wet 计入湿；type=dirty 计入脏；type=mixed 同时计入湿与脏（架构 §7.1）。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ...events.domain import ObservationEvent
from ..domain import DiaperProjection
from ._common import window_events


def project_diaper(
    events: Iterable[ObservationEvent], now: datetime
) -> DiaperProjection:
    """计算尿布派生指标（P0，纯函数）。"""
    recent = window_events(events, "diaper", now)
    wet = 0
    dirty = 0
    for e in recent:
        dtype = str(e.normalized_payload.get("type", "")).lower()
        if dtype == "wet":
            wet += 1
        elif dtype == "dirty":
            dirty += 1
        elif dtype == "mixed":
            wet += 1
            dirty += 1
    return DiaperProjection(wet_count_24h=wet, dirty_count_24h=dirty)


__all__ = ["project_diaper"]
