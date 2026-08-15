# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
#
# app/normalization/domain.py —— Normalization 领域类型与 event_type 常量（APC-T013）。
# 依据：ENGINEERING_DESIGN §2 M05（normalization：语音/图片/OCR/表单 → ObservationEvent；
#       置信度；去重）、§7.1（记录路径：NOTIFY events.changed → Normalization 写 feeding_log）；
#       ARCHITECTURE_FINAL §4.1；TASK_BACKLOG APC-T013。
# 设计：Normalization 消费 ObservationEvent，按 event_type 路由到 parser，产出
#       NormalizedRecord（派生表写入载荷），写 *_log 表并推进 processing_status。
#       P0 覆盖 feeding/diaper/sleep/temperature/supplement；不识别事件保留 observation_event
#       并标记 processing_status（不抛异常，架构 §7.1 不丢记录）。
# 边界：不做医疗判断（剂量/阈值在 rule_engine）；不产生告警等级（在 rule_engine/notification）；
#       派生表必须保留 event_id FK 溯源（架构 §6.1）。

"""Normalization 领域类型与 event_type 常量（APC-T013）。

架构（ENGINEERING_DESIGN §2 M05 / §7.1）：
Normalization 消费 ``ObservationEvent``，按 ``event_type`` 路由到 parser，
产出 ``NormalizedRecord``（派生表写入载荷），写 ``*_log`` 表并推进
``processing_status``（pending → normalized）。

P0 覆盖 ``feeding`` / ``diaper`` / ``sleep`` / ``temperature`` / ``supplement`` 五类。
不识别事件保留 ``observation_event`` 并标记 ``processing_status``（不抛异常，
架构 §7.1 不丢记录）。

边界：
    - 不做医疗判断（剂量/阈值在 rule_engine）。
    - 不产生告警等级（在 rule_engine/notification）。
    - 派生表必须保留 ``event_id`` FK 溯源（架构 §6.1）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# P0 支持的 event_type（架构 §7.1；TASK_BACKLOG APC-T013）。
# 不在此列的 event_type 不归一化，保留 observation_event 并标记 processing_status。
P0_EVENT_TYPES = frozenset({"feeding", "diaper", "sleep", "temperature", "supplement"})

# 派生表目标名（与 ORM logs.py 表名对齐）。
LogTable = Literal["feeding_log", "diaper_log", "sleep_log", "temperature_log", "supplement_log"]

# event_type → 派生表映射。
EVENT_TYPE_TO_TABLE: dict[str, LogTable] = {
    "feeding": "feeding_log",
    "diaper": "diaper_log",
    "sleep": "sleep_log",
    "temperature": "temperature_log",
    "supplement": "supplement_log",
}


@dataclass(frozen=True)
class NormalizedRecord:
    """归一化结果（派生表写入载荷）。

    ``event_id`` / ``baby_id``：溯源 FK（架构 §6.1，派生表必须含 event_id FK）。
    ``table``：目标派生表名（feeding_log 等）。
    ``structured``：结构化列（feeding_log 的 amount_ml/feeding_type/started_at/ended_at）；
        其余 log 表 P0 用最小结构，业务字段入 ``payload``。
    ``payload``：jsonb 兜底载荷（写入 *_log.payload）。
    ``confidence``：归一化置信度（manual=1.0，voice_text 可 <1.0，架构 §2 M05）。
    """

    event_id: str
    baby_id: str
    table: LogTable
    structured: dict[str, Any]
    payload: dict[str, Any]
    confidence: float


__all__ = [
    "EVENT_TYPE_TO_TABLE",
    "P0_EVENT_TYPES",
    "LogTable",
    "NormalizedRecord",
]
