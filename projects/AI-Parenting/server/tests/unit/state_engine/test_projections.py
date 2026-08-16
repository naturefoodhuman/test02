# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""State Engine P0 projection 单元测试（APC-T015）。

验证各 projection 边界场景 + project_state 聚合 + 幂等/确定性 property。
projection 为同步纯函数（无 async）。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from server.app.events.domain import ObservationEvent, ProcessingStatus, Source, SyncStatus
from server.app.state_engine import project_state
from server.app.state_engine.projections import (
    project_diaper,
    project_feeding,
    project_sleep,
    project_supplement,
    project_temperature,
)

NOW = datetime(2026, 8, 16, 8, 0, 0, tzinfo=UTC)
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"
FAM = "01HZXKQW7P0QJ9V8R3M4N6H5T4"


def _ev(
    event_type: str,
    *,
    start: datetime,
    payload: dict | None = None,
    end: datetime | None = None,
    is_deleted: bool = False,
    source: Source = Source.MANUAL,
) -> ObservationEvent:
    return ObservationEvent(
        event_id="01HZXKQW7P0QJ9V8R3M4N6H5T2",
        baby_id=BABY,
        family_id=FAM,
        event_type=event_type,
        start_time=start,
        end_time=end,
        client_created_at=start,
        server_received_at=start,
        normalized_payload=payload or {},
        source=source,
        sync_status=SyncStatus.SYNCED,
        processing_status=ProcessingStatus.NORMALIZED,
        is_deleted=is_deleted,
    )


# 唯一 event_id 避免领域模型校验冲突（ObservationEvent 不校验唯一性，但测试语义上每事件一个）。
_eid_counter = 0


def _next_eid() -> str:
    global _eid_counter
    _eid_counter += 1
    return f"01HZXKQW7P0QJ9V8R3M4N6{_eid_counter:05d}"


def _ev_unique(
    event_type: str,
    *,
    start: datetime,
    payload: dict | None = None,
    end: datetime | None = None,
    is_deleted: bool = False,
    source: Source = Source.MANUAL,
) -> ObservationEvent:
    return ObservationEvent(
        event_id=_next_eid(),
        baby_id=BABY,
        family_id=FAM,
        event_type=event_type,
        start_time=start,
        end_time=end,
        client_created_at=start,
        server_received_at=start,
        normalized_payload=payload or {},
        source=source,
        sync_status=SyncStatus.SYNCED,
        processing_status=ProcessingStatus.NORMALIZED,
        is_deleted=is_deleted,
    )


# ---- feeding ----


def test_feeding_empty_returns_none_ago():
    r = project_feeding([], NOW)
    assert r.last_feeding_ago_seconds is None
    assert r.volume_ml_24h == 0.0
    assert r.count_24h == 0


def test_feeding_last_ago_and_24h_volume_count():
    events = [
        _ev_unique("feeding", start=NOW - timedelta(hours=20), payload={"amount_ml": 100}),
        _ev_unique("feeding", start=NOW - timedelta(hours=3), payload={"amount_ml": 120}),
        _ev_unique("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 90}),
    ]
    r = project_feeding(events, NOW)
    assert r.last_feeding_ago_seconds == 3600.0  # 1h ago。
    assert r.volume_ml_24h == 310.0  # 100+120+90。
    assert r.count_24h == 3


def test_feeding_excludes_outside_window_and_deleted():
    events = [
        _ev_unique(
            "feeding", start=NOW - timedelta(hours=30), payload={"amount_ml": 200}
        ),  # 窗口外。
        _ev_unique(
            "feeding", start=NOW - timedelta(hours=2), payload={"amount_ml": 80}, is_deleted=True
        ),  # 已删。
        _ev_unique("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 60}),
    ]
    r = project_feeding(events, NOW)
    # last_ago 取所有未删除事件最近（含窗口外），距 now 1h。
    assert r.last_feeding_ago_seconds == 3600.0
    # 24h 窗口只含未删除 + 窗口内：60。
    assert r.volume_ml_24h == 60.0
    assert r.count_24h == 1


def test_feeding_skips_missing_amount_and_bool():
    events = [
        _ev_unique("feeding", start=NOW - timedelta(hours=1), payload={}),  # 无 amount。
        _ev_unique(
            "feeding", start=NOW - timedelta(minutes=30), payload={"amount_ml": True}
        ),  # bool 排除。
        _ev_unique("feeding", start=NOW - timedelta(minutes=10), payload={"amount_ml": 50}),
    ]
    r = project_feeding(events, NOW)
    assert r.volume_ml_24h == 50.0
    assert r.count_24h == 3  # count 计所有窗口内 feeding 事件（含缺 amount）。
    assert r.last_feeding_ago_seconds == 600.0  # 10min ago。


# ---- diaper ----


def test_diaper_wet_dirty_mixed_counts():
    events = [
        _ev_unique("diaper", start=NOW - timedelta(hours=5), payload={"type": "wet"}),
        _ev_unique("diaper", start=NOW - timedelta(hours=4), payload={"type": "dirty"}),
        _ev_unique("diaper", start=NOW - timedelta(hours=2), payload={"type": "mixed"}),
        _ev_unique("diaper", start=NOW - timedelta(hours=1), payload={"type": "wet"}),
    ]
    r = project_diaper(events, NOW)
    assert r.wet_count_24h == 3  # wet + mixed + wet。
    assert r.dirty_count_24h == 2  # dirty + mixed。


def test_diaper_excludes_outside_window_and_unknown_type():
    events = [
        _ev_unique("diaper", start=NOW - timedelta(hours=30), payload={"type": "wet"}),  # 窗口外。
        _ev_unique(
            "diaper", start=NOW - timedelta(hours=1), payload={"type": "unknown"}
        ),  # 未知 type 不计。
    ]
    r = project_diaper(events, NOW)
    assert r.wet_count_24h == 0
    assert r.dirty_count_24h == 0


# ---- temperature ----


def test_temperature_max_in_window():
    events = [
        _ev_unique("temperature", start=NOW - timedelta(hours=20), payload={"temperature_c": 37.2}),
        _ev_unique("temperature", start=NOW - timedelta(hours=5), payload={"temperature_c": 38.5}),
        _ev_unique("temperature", start=NOW - timedelta(hours=2), payload={"temperature_c": 36.8}),
    ]
    r = project_temperature(events, NOW)
    assert r.max_c_24h == 38.5


def test_temperature_empty_returns_none():
    r = project_temperature([], NOW)
    assert r.max_c_24h is None


def test_temperature_excludes_outside_window_and_invalid():
    events = [
        _ev_unique(
            "temperature", start=NOW - timedelta(hours=30), payload={"temperature_c": 39.0}
        ),  # 窗口外。
        _ev_unique(
            "temperature", start=NOW - timedelta(hours=1), payload={"temperature_c": "abc"}
        ),  # 非法。
        _ev_unique(
            "temperature", start=NOW - timedelta(minutes=30), payload={"temperature_c": True}
        ),  # bool 排除。
        _ev_unique(
            "temperature", start=NOW - timedelta(minutes=10), payload={"temperature_c": 37.5}
        ),
    ]
    r = project_temperature(events, NOW)
    assert r.max_c_24h == 37.5


# ---- sleep ----


def test_sleep_total_and_current_session():
    events = [
        _ev_unique("sleep", start=NOW - timedelta(hours=10), end=NOW - timedelta(hours=8)),  # 2h。
        _ev_unique("sleep", start=NOW - timedelta(hours=3), end=NOW - timedelta(hours=2)),  # 1h。
        _ev_unique("sleep", start=NOW - timedelta(minutes=30)),  # 进行中（未结束）。
    ]
    r = project_sleep(events, NOW)
    # 进行中会话 end 取 now：30min = 1800s；总 = 7200 + 3600 + 1800 = 12600。
    assert r.total_seconds_24h == 12600.0
    assert r.current_session_started_at == NOW - timedelta(minutes=30)


def test_sleep_empty():
    r = project_sleep([], NOW)
    assert r.total_seconds_24h == 0.0
    assert r.current_session_started_at is None


def test_sleep_overlap_with_window_edge():
    # 长睡眠跨越 24h 窗口左边界：start 在窗口外，end 在窗口内 → 只计窗口内部分。
    events = [
        _ev_unique("sleep", start=NOW - timedelta(hours=30), end=NOW - timedelta(hours=20)),
    ]
    r = project_sleep(events, NOW)
    # 窗口 [now-24h, now]，事件 [now-30h, now-20h]，交集 [now-24h, now-20h] = 4h = 14400s。
    assert r.total_seconds_24h == 14400.0
    assert r.current_session_started_at is None  # 已结束。


# ---- supplement ----


def test_supplement_last_ago_and_name():
    events = [
        _ev_unique("supplement", start=NOW - timedelta(hours=30), payload={"name": "维D"}),
        _ev_unique("supplement", start=NOW - timedelta(hours=2), payload={"name": "DHA"}),
    ]
    r = project_supplement(events, NOW)
    assert r.last_supplement_ago_seconds == 7200.0
    assert r.last_supplement_name == "DHA"


def test_supplement_empty():
    r = project_supplement([], NOW)
    assert r.last_supplement_ago_seconds is None
    assert r.last_supplement_name is None


def test_supplement_excludes_deleted():
    events = [
        _ev_unique(
            "supplement", start=NOW - timedelta(hours=1), payload={"name": "维D"}, is_deleted=True
        ),
        _ev_unique("supplement", start=NOW - timedelta(hours=5), payload={"name": "DHA"}),
    ]
    r = project_supplement(events, NOW)
    assert r.last_supplement_ago_seconds == 18000.0  # 5h ago（未删除的最近）。
    assert r.last_supplement_name == "DHA"


# ---- project_state 聚合 ----


def test_project_state_aggregates_all_and_source_range():
    events = [
        _ev_unique(
            "feeding", start=NOW - timedelta(hours=30), payload={"amount_ml": 100}
        ),  # 窗口外，最早。
        _ev_unique("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 120}),
        _ev_unique("diaper", start=NOW - timedelta(hours=2), payload={"type": "wet"}),
        _ev_unique("temperature", start=NOW - timedelta(hours=3), payload={"temperature_c": 37.8}),
        _ev_unique("sleep", start=NOW - timedelta(minutes=40)),  # 进行中，最晚 start。
        _ev_unique("supplement", start=NOW - timedelta(hours=4), payload={"name": "维D"}),
    ]
    state = project_state(events, NOW)
    assert state.feeding.volume_ml_24h == 120.0  # 窗口外不计。
    assert state.feeding.count_24h == 1
    assert state.diaper.wet_count_24h == 1
    assert state.temperature.max_c_24h == 37.8
    assert state.sleep.current_session_started_at == NOW - timedelta(minutes=40)
    assert state.supplement.last_supplement_name == "维D"
    assert state.computed_at == NOW
    # source_event_range：最早 feeding(30h ago) ~ 最晚 sleep(40min ago)。
    assert state.source_event_range[0] == NOW - timedelta(hours=30)
    assert state.source_event_range[1] == NOW - timedelta(minutes=40)


def test_project_state_empty_events():
    state = project_state([], NOW)
    assert state.feeding.last_feeding_ago_seconds is None
    assert state.diaper.wet_count_24h == 0
    assert state.sleep.current_session_started_at is None
    assert state.temperature.max_c_24h is None
    assert state.supplement.last_supplement_name is None
    assert state.source_event_range == (None, None)


def test_project_state_to_snapshot_serializable():
    events = [_ev_unique("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 90})]
    state = project_state(events, NOW)
    snap = state.to_snapshot()
    assert snap["feeding"]["volume_ml_24h"] == 90.0
    assert snap["feeding"]["count_24h"] == 1
    assert snap["sleep"]["current_session_started_at"] is None
    assert snap["source_event_range"][0] is not None
    assert isinstance(snap["source_event_range"][0], str)


# ---- property：确定性 / 幂等 ----


@given(st.data())
@settings(max_examples=20)
def test_project_state_deterministic(data):
    """同一事件集多次投影结果一致（纯函数确定性）。"""
    n = data.draw(st.integers(min_value=0, max_value=5))
    offsets = data.draw(
        st.lists(
            st.floats(min_value=0, max_value=23, allow_nan=False, allow_infinity=False),
            min_size=n,
            max_size=n,
        )
    )
    events = [
        _ev_unique("feeding", start=NOW - timedelta(hours=o), payload={"amount_ml": 100})
        for o in offsets
    ]
    s1 = project_state(events, NOW)
    s2 = project_state(events, NOW)
    assert s1 == s2
