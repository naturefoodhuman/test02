# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""StateEngine 单元测试（APC-T016）。

用 Fake repo/loader 验证重算幂等、processing_status 推进 projected、get_state 只读。
不依赖 DB（DB 链路在 integration 测试覆盖）。asyncio_mode=auto，测试用 async 函数。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from server.app.common.clock import FixedClock
from server.app.events.domain import ObservationEvent, ProcessingStatus, Source, SyncStatus
from server.app.state_engine.domain import DerivedBabyState
from server.app.state_engine.engine import StateEngine

NOW = datetime(2026, 8, 16, 8, 0, 0, tzinfo=UTC)
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"
FAM = "01HZXKQW7P0QJ9V8R3M4N6H5T4"


def _ev(
    event_type: str,
    *,
    start: datetime,
    payload: dict | None = None,
    processing_status: ProcessingStatus = ProcessingStatus.NORMALIZED,
    eid: str = "01HZXKQW7P0QJ9V8R3M4N6H5T2",
) -> ObservationEvent:
    return ObservationEvent(
        event_id=eid,
        baby_id=BABY,
        family_id=FAM,
        event_type=event_type,
        start_time=start,
        client_created_at=start,
        server_received_at=start,
        normalized_payload=payload or {},
        source=Source.MANUAL,
        sync_status=SyncStatus.SYNCED,
        processing_status=processing_status,
    )


class FakeEventLoader:
    def __init__(self, events: list[ObservationEvent]) -> None:
        self._events = events

    async def load_by_baby(self, baby_id: str) -> list[ObservationEvent]:
        return [e for e in self._events if e.baby_id == baby_id]


class FakeSnapshotRepo:
    def __init__(self) -> None:
        self.store: dict[str, DerivedBabyState] = {}
        self.upserts = 0

    async def upsert(self, baby_id: str, state: DerivedBabyState) -> None:
        self.store[baby_id] = state
        self.upserts += 1

    async def get(self, baby_id: str) -> DerivedBabyState | None:
        return self.store.get(baby_id)


class FakeEventRepo:
    def __init__(self) -> None:
        self.advanced: list[tuple[str, ProcessingStatus]] = []

    async def update_processing_status(
        self, event_id: str, status: ProcessingStatus
    ) -> ObservationEvent | None:
        self.advanced.append((event_id, status))
        return None


def _engine(
    events: list[ObservationEvent], *, now: datetime = NOW
) -> tuple[StateEngine, FakeSnapshotRepo, FakeEventRepo]:
    snap = FakeSnapshotRepo()
    repo = FakeEventRepo()
    engine = StateEngine(
        event_loader=FakeEventLoader(events),
        snapshot_repo=snap,
        event_repo=repo,
        clock=FixedClock(now),
    )
    return engine, snap, repo


async def test_recompute_upserts_snapshot_and_advances_projected():
    events = [
        _ev("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 120}, eid="01HZXKQW7P0QJ9V8R3M4N6H5A1"),
        _ev("diaper", start=NOW - timedelta(hours=2), payload={"type": "wet"}, eid="01HZXKQW7P0QJ9V8R3M4N6H5A2"),
    ]
    engine, snap, repo = _engine(events)

    state = await engine.recompute(BABY)

    assert snap.upserts == 1
    assert snap.store[BABY] is state
    assert state.feeding.volume_ml_24h == 120.0
    assert state.diaper.wet_count_24h == 1
    # 两事件均从 normalized 推进到 projected。
    assert repo.advanced == [
        ("01HZXKQW7P0QJ9V8R3M4N6H5A1", ProcessingStatus.PROJECTED),
        ("01HZXKQW7P0QJ9V8R3M4N6H5A2", ProcessingStatus.PROJECTED),
    ]


async def test_recompute_idempotent_same_input_same_output():
    events = [
        _ev("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 90}, eid="01HZXKQW7P0QJ9V8R3M4N6H5B1"),
    ]
    engine, snap, _ = _engine(events)

    s1 = await engine.recompute(BABY)
    s2 = await engine.recompute(BABY)

    assert snap.upserts == 2  # 两次 upsert（覆盖）。
    assert s1 == s2  # 内容一致（幂等）。


async def test_recompute_skips_already_projected_for_status_advance():
    events = [
        _ev(
            "feeding",
            start=NOW - timedelta(hours=1),
            payload={"amount_ml": 60},
            processing_status=ProcessingStatus.PROJECTED,
            eid="01HZXKQW7P0QJ9V8R3M4N6H5C1",
        ),
    ]
    engine, _, repo = _engine(events)

    await engine.recompute(BABY)

    # 已 projected 的事件不再推进。
    assert repo.advanced == []


async def test_recompute_empty_events_still_upserts_snapshot():
    engine, snap, _ = _engine([])

    state = await engine.recompute(BABY)

    assert snap.upserts == 1
    assert state.feeding.last_feeding_ago_seconds is None
    assert state.source_event_range == (None, None)


async def test_get_state_returns_none_when_no_snapshot():
    engine, snap, _ = _engine([])

    r = await engine.get_state(BABY)
    assert r is None
    assert snap.upserts == 0  # get 不触发 upsert。


async def test_get_state_returns_upserted_snapshot():
    events = [
        _ev("feeding", start=NOW - timedelta(hours=1), payload={"amount_ml": 100}, eid="01HZXKQW7P0QJ9V8R3M4N6H5D1")
    ]
    engine, _, _ = _engine(events)

    await engine.recompute(BABY)
    r = await engine.get_state(BABY)
    assert r is not None
    assert r.feeding.volume_ml_24h == 100.0
