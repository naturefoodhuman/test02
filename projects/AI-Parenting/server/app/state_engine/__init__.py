# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-02 00:00:00
"""State Engine 模块（APC-T015）。

Baby State Engine：消费 ``ObservationEvent`` 增量，派生 ``DerivedBabyState`` 快照
（架构 §10.1）。只派生不告警（告警等级在 rule_engine/notification）。

APC-T015：P0 projection 纯函数（feeding/diaper/sleep/temperature/supplement）+ 聚合入口。
APC-T016：增量重算 + snapshot repo upsert + State API（后续）。
"""

from .domain import (
    DerivedBabyState,
    DiaperProjection,
    FeedingProjection,
    SleepProjection,
    SupplementProjection,
    TemperatureProjection,
)
from .project import project_state

__all__ = [
    "DerivedBabyState",
    "DiaperProjection",
    "FeedingProjection",
    "SleepProjection",
    "SupplementProjection",
    "TemperatureProjection",
    "project_state",
]
