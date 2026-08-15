# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
#
# app/normalization/parsers/form.py —— 表单解析（manual source，APC-T013）。
# 依据：ENGINEERING_DESIGN §2 M05、§7.1；TASK_BACKLOG APC-T013。
# 设计：manual 表单的 ObservationEvent.normalized_payload 已结构化（App 端表单采集），
#       form parser 直接按 event_type 映射到 NormalizedRecord，confidence=1.0（manual）。
#       不做医疗判断；缺关键字段时 confidence 降低但不抛异常（保留事件，标记 processing_status）。
# 边界：只做字段映射与轻量校验（类型/范围），不调用 LLM、不查 DB、不产生告警。

"""表单解析（manual source，APC-T013）。

manual 表单的 ``ObservationEvent.normalized_payload`` 已由 App 端表单采集为结构化
JSON（架构 §7.1：App 本地 Logger 解析 → 轻确认 → INSERT event）。
form parser 直接按 ``event_type`` 映射到 ``NormalizedRecord``，``confidence=1.0``
（架构 §2 M05：manual=1.0）。

P0 覆盖 feeding/diaper/sleep/temperature/supplement。缺关键字段时 ``confidence``
降低但不抛异常（保留事件，标记 ``processing_status``，架构 §7.1 不丢记录）。

边界：只做字段映射与轻量校验（类型/范围），不调用 LLM、不查 DB、不产生告警。
"""

from __future__ import annotations

from typing import Any

from ..domain import EVENT_TYPE_TO_TABLE, P0_EVENT_TYPES, LogTable, NormalizedRecord

# manual 表单置信度（架构 §2 M05）。
MANUAL_CONFIDENCE = 1.0
# 缺关键字段时的降级置信度（仍归一化，但标记低置信供下游判断）。
PARTIAL_CONFIDENCE = 0.6


def parse_form(
    *,
    event_id: str,
    baby_id: str,
    event_type: str,
    normalized_payload: dict[str, Any],
    start_time: Any,
    end_time: Any | None = None,
) -> NormalizedRecord | None:
    """解析 manual 表单事件 → NormalizedRecord（confidence=1.0）。

    Args:
        event_id: 事件 ULID（溯源 FK）。
        baby_id: 婴儿 ULID。
        event_type: 事件类型（须在 P0_EVENT_TYPES 内，否则返回 None）。
        normalized_payload: App 表单采集的结构化载荷。
        start_time: 事件开始时间（写入 feeding_log.started_at）。
        end_time: 事件结束时间（写入 feeding_log.ended_at，可选）。

    Returns:
        ``NormalizedRecord``；event_type 不在 P0 范围返回 ``None``（调用方保留事件）。
    """
    if event_type not in P0_EVENT_TYPES:
        return None
    table: LogTable = EVENT_TYPE_TO_TABLE[event_type]
    structured = _extract_structured(event_type, normalized_payload, start_time, end_time)
    confidence = MANUAL_CONFIDENCE
    # 缺关键字段降级（仍归一化，不丢记录）。
    if not _has_required_fields(event_type, normalized_payload):
        confidence = PARTIAL_CONFIDENCE
    return NormalizedRecord(
        event_id=event_id,
        baby_id=baby_id,
        table=table,
        structured=structured,
        payload=dict(normalized_payload),
        confidence=confidence,
    )


def _extract_structured(
    event_type: str,
    payload: dict[str, Any],
    start_time: Any,
    end_time: Any | None,
) -> dict[str, Any]:
    """提取派生表结构化列（feeding_log 有结构化列；其余 P0 用 payload 兜底）。

    feeding_log 结构化列（ORM logs.py）：amount_ml / feeding_type / started_at / ended_at。
    其余 log 表 P0 最小结构（event_id + baby_id + payload jsonb），无额外结构化列。
    """
    if event_type == "feeding":
        return {
            "amount_ml": _as_int(payload.get("amount_ml")),
            "feeding_type": _as_str(payload.get("feeding_type")),
            "started_at": start_time,
            "ended_at": end_time,
        }
    # diaper/sleep/temperature/supplement：P0 无结构化列，业务字段入 payload jsonb。
    return {}


def _has_required_fields(event_type: str, payload: dict[str, Any]) -> bool:
    """检查 event_type 的关键字段是否齐全（轻量校验，非医疗判断）。"""
    if event_type == "feeding":
        return payload.get("amount_ml") is not None
    if event_type == "diaper":
        return payload.get("type") is not None  # wet/dirty/mixed
    if event_type == "sleep":
        return True  # sleep 仅需 start_time（事件层已保证）
    if event_type == "temperature":
        return payload.get("value_c") is not None
    if event_type == "supplement":
        return payload.get("name") is not None or payload.get("supplement_name") is not None
    return True


def _as_int(val: Any) -> int | None:
    if isinstance(val, bool):  # bool 是 int 子类，排除。
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return None


def _as_str(val: Any) -> str | None:
    return val if isinstance(val, str) else None


__all__ = ["MANUAL_CONFIDENCE", "PARTIAL_CONFIDENCE", "parse_form"]
