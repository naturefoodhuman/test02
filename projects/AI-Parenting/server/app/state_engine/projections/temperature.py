# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/projections/temperature.py —— 体温派生指标（APC-T015）。
# 依据：ARCHITECTURE_FINAL §10.1（24h 最高温）；TASK_BACKLOG APC-T015。
# 设计：纯函数，输入未删除 temperature 事件 + now，输出 TemperatureProjection。
#       体温取 normalized_payload.temperature_c（℃）。
# 边界：只计算不告警（体温阈值告警在 rule_engine，T021）。

"""体温派生指标（APC-T015）。

纯函数：输入未删除 ``temperature`` 事件集合 + 参考时间 ``now``，输出 ``TemperatureProjection``：
    - ``max_c_24h``：近 24h 最高体温（℃）；无记录 None。
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ...events.domain import ObservationEvent
from ..domain import TemperatureProjection
from ._common import window_events


def project_temperature(
    events: Iterable[ObservationEvent], now: datetime
) -> TemperatureProjection:
    """计算体温派生指标（P0，纯函数）。"""
    recent = window_events(events, "temperature", now)
    max_c: float | None = None
    for e in recent:
        temp = e.normalized_payload.get("temperature_c")
        if isinstance(temp, bool) or temp is None:
            continue
        try:
            temp_f = float(temp)
        except (TypeError, ValueError):
            continue
        if max_c is None or temp_f > max_c:
            max_c = temp_f
    return TemperatureProjection(max_c_24h=max_c)


__all__ = ["project_temperature"]
