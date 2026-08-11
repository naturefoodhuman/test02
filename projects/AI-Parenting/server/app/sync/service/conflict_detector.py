# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/sync/service/conflict_detector.py —— 同步冲突软提示（APC-T012）。
# 依据：ARCHITECTURE_FINAL §9.2（5 分钟内疑似重复喂奶 → 不自动删，UI 软提示；
#       同事件并发编辑 → 保留版本，最后编辑为当前；离线重复 → 上线合并提示）；
#       ENGINEERING_DESIGN §4（powersync-service 不做业务级冲突裁决，由应用层判定）；
#       TASK_BACKLOG APC-T012（5 分钟内疑似重复喂奶仅生成软提示，不自动删除）。
# 设计：应用层在 EventService.record 后调用 detect_duplicate_feeding，对同 baby 5 分钟内
#       的 feeding 生成 ConflictHint（软提示），不自动删除（§9.2）。
#       疑似判定：同 baby_id + 同 event_type=feeding + start_time 间隔 ≤ 5 分钟 +
#       amount_ml 接近（差 ≤ 30ml 或相同）——离线重复/误触典型模式。
# 边界：只生成软提示，不修改事件（不自动删/不合并）；冲突合并需 Admin 二次确认（§9.2）。

"""同步冲突软提示（APC-T012）。

架构（ARCHITECTURE_FINAL §9.2 / ENGINEERING_DESIGN §4）：
PowerSync 不做业务级冲突裁决（架构 §4），由应用层监听 PG 变更按 §9.2 规则处理。
本模块实现"5 分钟内疑似重复喂奶 → 软提示"规则（§9.2）：

    - 同 baby + 同 event_type=feeding + start_time 间隔 ≤ 5 分钟 + amount 接近
      → 生成 ``ConflictHint``（软提示），**不自动删除**（§9.2）。
    - 冲突合并需 Admin 二次确认（§9.2：医疗/系统规则冲突 → Admin 二次确认并记录版本）。

P0 阶段：仅生成软提示（写入日志 / 返回给调用方），UI 软提示在 Android 端实现（APC-T047+）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from ...events.domain import ObservationEvent

# §9.2：5 分钟内疑似重复喂奶窗口。
DUPLICATE_FEEDING_WINDOW = timedelta(minutes=5)
# amount 接近阈值（ml）：差 ≤ 30ml 视为接近（离线重复/误触典型）。
AMOUNT_SIMILAR_THRESHOLD = 30.0


@dataclass(frozen=True)
class ConflictHint:
    """冲突软提示（§9.2，不自动删除）。

    ``new_event_id`` —— 新事件（触发检测）。
    ``existing_event_id`` —— 疑似重复的既有事件。
    ``kind`` —— 冲突类型（duplicate_feeding 等）。
    ``detail`` —— 软提示详情（供 UI 展示与 Admin 确认）。
    """

    new_event_id: str
    existing_event_id: str
    kind: str
    detail: dict[str, Any]


def _amount_ml(ev: ObservationEvent) -> float | None:
    """从 normalized_payload 取 amount_ml（feeding 事件）。"""
    val = ev.normalized_payload.get("amount_ml")
    if isinstance(val, int | float):
        return float(val)
    return None


def detect_duplicate_feeding(
    new_event: ObservationEvent,
    recent_events: list[ObservationEvent],
) -> ConflictHint | None:
    """检测 5 分钟内疑似重复 feeding（§9.2 软提示，不自动删）。

    Args:
        new_event: 新写入的 feeding 事件。
        recent_events: 同 baby 的近期 feeding 事件（按 start_time DESC，调用方过滤）。

    Returns:
        命中则返回 ``ConflictHint``；否则 ``None``。命中**不修改**任何事件（§9.2）。
    """
    if new_event.event_type != "feeding":
        return None
    new_amount = _amount_ml(new_event)
    if new_amount is None:
        return None

    for ev in recent_events:
        if ev.event_id == new_event.event_id:
            continue
        if ev.is_deleted:
            continue
        # 时间间隔 ≤ 5 分钟（取绝对值，新旧顺序无关）。
        delta = abs((new_event.start_time - ev.start_time).total_seconds())
        if delta > DUPLICATE_FEEDING_WINDOW.total_seconds():
            continue
        existing_amount = _amount_ml(ev)
        if existing_amount is None:
            continue
        if abs(new_amount - existing_amount) <= AMOUNT_SIMILAR_THRESHOLD:
            return ConflictHint(
                new_event_id=new_event.event_id,
                existing_event_id=ev.event_id,
                kind="duplicate_feeding",
                detail={
                    "window_minutes": DUPLICATE_FEEDING_WINDOW.total_seconds() / 60,
                    "delta_seconds": delta,
                    "new_amount_ml": new_amount,
                    "existing_amount_ml": existing_amount,
                    "hint": "5 分钟内疑似重复喂奶，请确认是否合并（§9.2 软提示，不自动删除）",
                },
            )
    return None


__all__ = [
    "AMOUNT_SIMILAR_THRESHOLD",
    "DUPLICATE_FEEDING_WINDOW",
    "ConflictHint",
    "detect_duplicate_feeding",
]
