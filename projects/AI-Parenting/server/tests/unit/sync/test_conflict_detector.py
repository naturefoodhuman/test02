# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-12 00:00:00
"""同步冲突软提示单元测试（APC-T012 测试要求：5 分钟内重复 feeding 生成 conflict hint）。

验证 ``detect_duplicate_feeding``：
    - 5 分钟内同 baby、amount 接近（差 ≤ 30ml）→ ConflictHint（不自动删）。
    - 超过 5 分钟窗口 → None。
    - amount 差 > 30ml → None。
    - 非 feeding 事件 → None。
    - amount_ml 缺失 → None。
    - 软删除事件被跳过。
    - 自身（同 event_id）被跳过。
    - 命中不修改任何事件（§9.2 不自动删除）。

依据：ARCHITECTURE_FINAL §9.2；TASK_BACKLOG APC-T012。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from server.app.events.domain import ObservationEvent, Source
from server.app.sync.service.conflict_detector import (
    AMOUNT_SIMILAR_THRESHOLD,
    DUPLICATE_FEEDING_WINDOW,
    detect_duplicate_feeding,
)

NOW = datetime(2026, 8, 11, 8, 0, 0, tzinfo=UTC)


def _feeding(event_id: str, amount_ml: float, start: datetime, **extra) -> ObservationEvent:
    """构造 feeding ObservationEvent。"""
    return ObservationEvent(
        event_id=event_id,
        baby_id="01HZXKQW7P0QJ9V8R3M4N6H5T3",
        family_id="01HZXKQW7P0QJ9V8R3M4N6H5T4",
        event_type="feeding",
        start_time=start,
        client_created_at=start,
        server_received_at=start,
        normalized_payload={"amount_ml": amount_ml},
        source=Source.MANUAL,
        **extra,
    )


# ---- 命中 ----


def test_duplicate_within_5min_similar_amount_returns_hint():
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    existing = _feeding("01HZOLD00000000000000001", 130, NOW - timedelta(minutes=2))
    hint = detect_duplicate_feeding(new, [existing])
    assert hint is not None
    assert hint.new_event_id == "01HZNEW00000000000000001"
    assert hint.existing_event_id == "01HZOLD00000000000000001"
    assert hint.kind == "duplicate_feeding"
    assert hint.detail["new_amount_ml"] == 120
    assert hint.detail["existing_amount_ml"] == 130
    assert hint.detail["window_minutes"] == 5.0


def test_duplicate_exact_boundary_5min_returns_hint():
    """恰好 5 分钟（边界）→ 命中（≤ 5 分钟）。"""
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    existing = _feeding("01HZOLD00000000000000001", 120, NOW - DUPLICATE_FEEDING_WINDOW)
    hint = detect_duplicate_feeding(new, [existing])
    assert hint is not None


def test_duplicate_new_before_existing_returns_hint():
    """新旧顺序无关（取绝对值间隔）。"""
    new = _feeding("01HZNEW00000000000000001", 120, NOW - timedelta(minutes=3))
    existing = _feeding("01HZOLD00000000000000001", 120, NOW)
    hint = detect_duplicate_feeding(new, [existing])
    assert hint is not None


def test_duplicate_amount_threshold_boundary_returns_hint():
    """amount 差恰好 30ml（边界）→ 命中（≤ 30ml）。"""
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    existing = _feeding("01HZOLD00000000000000001", 150, NOW - timedelta(minutes=1))
    hint = detect_duplicate_feeding(new, [existing])
    assert hint is not None
    assert (
        abs(hint.detail["new_amount_ml"] - hint.detail["existing_amount_ml"])
        == AMOUNT_SIMILAR_THRESHOLD
    )


# ---- 不命中 ----


def test_beyond_5min_returns_none():
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    existing = _feeding("01HZOLD00000000000000001", 120, NOW - timedelta(minutes=6))
    assert detect_duplicate_feeding(new, [existing]) is None


def test_amount_diff_exceeds_threshold_returns_none():
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    existing = _feeding("01HZOLD00000000000000001", 200, NOW - timedelta(minutes=1))
    assert detect_duplicate_feeding(new, [existing]) is None


def test_non_feeding_event_returns_none():
    new = ObservationEvent(
        event_id="01HZNEW00000000000000001",
        baby_id="01HZXKQW7P0QJ9V8R3M4N6H5T3",
        family_id="01HZXKQW7P0QJ9V8R3M4N6H5T4",
        event_type="diaper",
        start_time=NOW,
        client_created_at=NOW,
        server_received_at=NOW,
        normalized_payload={"amount_ml": 120},
        source=Source.MANUAL,
    )
    existing = _feeding("01HZOLD00000000000000001", 120, NOW - timedelta(minutes=1))
    assert detect_duplicate_feeding(new, [existing]) is None


def test_new_event_missing_amount_returns_none():
    new = ObservationEvent(
        event_id="01HZNEW00000000000000001",
        baby_id="01HZXKQW7P0QJ9V8R3M4N6H5T3",
        family_id="01HZXKQW7P0QJ9V8R3M4N6H5T4",
        event_type="feeding",
        start_time=NOW,
        client_created_at=NOW,
        server_received_at=NOW,
        normalized_payload={},  # 无 amount_ml
        source=Source.MANUAL,
    )
    existing = _feeding("01HZOLD00000000000000001", 120, NOW - timedelta(minutes=1))
    assert detect_duplicate_feeding(new, [existing]) is None


def test_existing_event_missing_amount_skipped():
    """既有事件无 amount_ml → 跳过该条，继续找下一条。"""
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    no_amount = ObservationEvent(
        event_id="01HZNOAMOUNT00000000000001",
        baby_id="01HZXKQW7P0QJ9V8R3M4N6H5T3",
        family_id="01HZXKQW7P0QJ9V8R3M4N6H5T4",
        event_type="feeding",
        start_time=NOW - timedelta(minutes=1),
        client_created_at=NOW - timedelta(minutes=1),
        server_received_at=NOW - timedelta(minutes=1),
        normalized_payload={},
        source=Source.MANUAL,
    )
    good = _feeding("01HZGOOD00000000000000001", 120, NOW - timedelta(minutes=2))
    hint = detect_duplicate_feeding(new, [no_amount, good])
    assert hint is not None
    assert hint.existing_event_id == "01HZGOOD00000000000000001"


def test_soft_deleted_existing_skipped():
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    deleted = _feeding("01HZOLD00000000000000001", 120, NOW - timedelta(minutes=1), is_deleted=True)
    assert detect_duplicate_feeding(new, [deleted]) is None


def test_self_event_skipped():
    """recent_events 含 new_event 自身（如查询未排除）→ 跳过，不与自身冲突。"""
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    # 同 event_id 的条目不应触发自冲突。
    self_copy = _feeding("01HZNEW00000000000000001", 120, NOW)
    assert detect_duplicate_feeding(new, [self_copy]) is None


def test_empty_recent_returns_none():
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    assert detect_duplicate_feeding(new, []) is None


# ---- 不修改事件（§9.2 不自动删）----


def test_hint_does_not_modify_events():
    """命中后只返回 ConflictHint，不修改 new/existing 事件（§9.2 不自动删除）。"""
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    existing = _feeding("01HZOLD00000000000000001", 120, NOW - timedelta(minutes=1))
    hint = detect_duplicate_feeding(new, [existing])
    assert hint is not None
    # 两条事件均未被软删除（不自动删）。
    assert new.is_deleted is False
    assert existing.is_deleted is False
    # payload 未被改动。
    assert new.normalized_payload == {"amount_ml": 120}
    assert existing.normalized_payload == {"amount_ml": 120}


# ---- 多条近期事件，取第一个命中 ----


def test_multiple_recent_returns_first_match():
    new = _feeding("01HZNEW00000000000000001", 120, NOW)
    far = _feeding("01HZFAR00000000000000001", 120, NOW - timedelta(minutes=10))  # 超窗口
    near = _feeding("01HZNEAR00000000000000001", 130, NOW - timedelta(minutes=1))  # 命中
    hint = detect_duplicate_feeding(new, [far, near])
    assert hint is not None
    assert hint.existing_event_id == "01HZNEAR00000000000000001"
