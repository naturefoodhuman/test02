# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/projections/feeding.py —— 喂奶派生指标（APC-T015）。
# 依据：ARCHITECTURE_FINAL §10.1（距上次喂奶、24h 奶量/次数）；
#       TASK_BACKLOG APC-T015。
# 设计：纯函数，输入未删除 feeding 事件集合 + now，输出 FeedingProjection。
#       amount_ml 取 normalized_payload.amount_ml（manual 表单结构化，voice 解析后入同字段）。
# 边界：只计算不告警；不读派生表（消费事件本身）。

"""喂奶派生指标（APC-T015）。

纯函数：输入未删除 ``feeding`` 事件集合 + 参考时间 ``now``，输出 ``FeedingProjection``：
    - ``last_feeding_ago_seconds``：最近 feeding 事件 start_time 距 now 秒数（无记录 None）。
    - ``volume_ml_24h``：近 24h feeding 事件 amount_ml 之和。
    - ``count_24h``：近 24h feeding 事件次数。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ...events.domain import ObservationEvent
from ..domain import FeedingProjection
from ._common import active_events, seconds_between, window_events


def project_feeding(events: Iterable[ObservationEvent], now: datetime) -> FeedingProjection:
    """计算喂奶派生指标（P0，纯函数）。"""
    active = active_events(events, "feeding")
    if not active:
        return FeedingProjection(last_feeding_ago_seconds=None, volume_ml_24h=0.0, count_24h=0)
    last = active[-1]
    last_ago = seconds_between(last.start_time, now)
    recent = window_events(events, "feeding", now)
    volume = 0.0
    for e in recent:
        amount = e.normalized_payload.get("amount_ml")
        if isinstance(amount, bool) or amount is None:
            continue  # bool 是 int 子类，排除；缺 amount 跳过。
        volume += float(amount)
    return FeedingProjection(
        last_feeding_ago_seconds=last_ago,
        volume_ml_24h=volume,
        count_24h=len(recent),
    )


__all__ = ["project_feeding"]
