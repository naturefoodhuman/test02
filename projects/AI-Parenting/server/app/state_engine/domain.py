# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/domain.py —— Baby State Engine 领域类型（APC-T015）。
# 依据：ENGINEERING_DESIGN §2 M06（state_engine：事件驱动增量派生 DerivedBabyState；幂等重算）、
#       §3 state_engine；ARCHITECTURE_FINAL §10.1（DerivedBabyState 输出字段）、§6.1（derived_baby_state 表）；
#       TASK_BACKLOG APC-T015（P0 projection 纯函数；只计算不产生告警等级；覆盖率 ≥95%）。
# 设计：DerivedBabyState snapshot 为 dataclass，承载 P0 派生指标（feeding/diaper/sleep/temperature/supplement）。
#       T015 只做 projection 纯函数，不写 DB（upsert 在 T016）。输入 ObservationEvent 集合 + 参考时间 now。
# 边界：只派生不告警（告警等级在 rule_engine/notification）；不做医疗判断；不读派生表（消费事件本身）。

"""Baby State Engine 领域类型（APC-T015）。

架构（ENGINEERING_DESIGN §2 M06 / §3 / ARCHITECTURE_FINAL §10.1）：
State Engine 消费 ``ObservationEvent`` 增量，派生 ``DerivedBabyState`` 快照。
本模块定义 P0 快照结构（feeding/diaper/sleep/temperature/supplement 指标）。

T015 只做 projection 纯函数（输入事件集 + 参考时间 → 指标），不写 DB
（``derived_baby_state`` upsert 在 APC-T016）。只派生不告警（告警等级在
rule_engine/notification，架构 §10）；不做医疗判断。

输入源：``ObservationEvent``（事件本身，非派生表——派生表是 normalization 产物 + 溯源，
State Engine 消费事件，架构 §10.1 输入"ObservationEvent 增量"）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FeedingProjection:
    """喂奶派生指标（P0）。

    ``last_feeding_ago_seconds``：距上次喂奶秒数（最近未删除 feeding 事件 start_time 距 now；
        无记录为 None）。T016 起供"距上次喂奶"展示与提醒。
    ``volume_ml_24h``：近 24h 喂奶总量（ml，未删除 feeding 事件 amount_ml 之和）。
    ``count_24h``：近 24h 喂奶次数。
    """

    last_feeding_ago_seconds: float | None
    volume_ml_24h: float
    count_24h: int


@dataclass(frozen=True)
class DiaperProjection:
    """尿布派生指标（P0）。

    ``wet_count_24h`` / ``dirty_count_24h``：近 24h 湿/脏尿布次数（按 normalized_payload.type）。
    type 取值：wet / dirty / mixed（mixed 同时计入湿与脏，架构 §7.1 voice parser 产出）。
    """

    wet_count_24h: int
    dirty_count_24h: int


@dataclass(frozen=True)
class SleepProjection:
    """睡眠派生指标（P0）。

    ``total_seconds_24h``：近 24h 睡眠总秒数（sleep 事件 [start,end] 与 24h 窗口交集之和；
        未结束事件 end 取 now）。
    ``current_session_started_at``：当前进行中会话的 start_time（未结束 sleep 事件）；
        无进行中会话为 None。
    """

    total_seconds_24h: float
    current_session_started_at: datetime | None


@dataclass(frozen=True)
class TemperatureProjection:
    """体温派生指标（P0）。

    ``max_c_24h``：近 24h 最高体温（℃）；无记录为 None。
    """

    max_c_24h: float | None


@dataclass(frozen=True)
class SupplementProjection:
    """补剂派生指标（P0）。

    ``last_supplement_ago_seconds``：距上次补剂秒数（最近未删除 supplement 事件 start_time 距 now；
        无记录为 None）。
    ``last_supplement_name``：上次补剂名称（normalized_payload.name）；无记录为 None。
    """

    last_supplement_ago_seconds: float | None
    last_supplement_name: str | None


@dataclass(frozen=True)
class DerivedBabyState:
    """P0 派生宝宝状态快照（APC-T015）。

    承载 feeding/diaper/sleep/temperature/supplement P0 指标。T016 起序列化为
    ``derived_baby_state.snapshot`` jsonb + ``computed_at`` upsert。
    ``computed_at``：快照计算时间（参考时间 now，T016 写入）。
    ``source_event_range``：参与重算的事件时间范围（最早/最晚 start_time），便于审计追溯
    （架构 §6.3 snapshot 含 computed_at 与 source event range）。
    """

    feeding: FeedingProjection
    diaper: DiaperProjection
    sleep: SleepProjection
    temperature: TemperatureProjection
    supplement: SupplementProjection
    computed_at: datetime
    source_event_range: tuple[datetime | None, datetime | None] = field(default=(None, None))

    def to_snapshot(self) -> dict[str, Any]:
        """序列化为 ``derived_baby_state.snapshot`` jsonb（T016 写入用）。"""
        rng = self.source_event_range
        return {
            "feeding": {
                "last_feeding_ago_seconds": self.feeding.last_feeding_ago_seconds,
                "volume_ml_24h": self.feeding.volume_ml_24h,
                "count_24h": self.feeding.count_24h,
            },
            "diaper": {
                "wet_count_24h": self.diaper.wet_count_24h,
                "dirty_count_24h": self.diaper.dirty_count_24h,
            },
            "sleep": {
                "total_seconds_24h": self.sleep.total_seconds_24h,
                "current_session_started_at": (
                    self.sleep.current_session_started_at.isoformat()
                    if self.sleep.current_session_started_at is not None
                    else None
                ),
            },
            "temperature": {"max_c_24h": self.temperature.max_c_24h},
            "supplement": {
                "last_supplement_ago_seconds": self.supplement.last_supplement_ago_seconds,
                "last_supplement_name": self.supplement.last_supplement_name,
            },
            "source_event_range": [
                rng[0].isoformat() if rng[0] is not None else None,
                rng[1].isoformat() if rng[1] is not None else None,
            ],
        }


__all__ = [
    "DerivedBabyState",
    "DiaperProjection",
    "FeedingProjection",
    "SleepProjection",
    "SupplementProjection",
    "TemperatureProjection",
]
