# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""EventService 用例服务单元测试（APC-T009 测试要求：Unit 幂等语义）。

验证 ``EventService``：
    - record：合法事件写入；server_received_at 由 Clock 填充；非法 ULID → ValidationError。
    - 幂等：重复同一 event_id 返回既有记录，不创建重复行（Fake 仓储计数验证）。
    - correct：correction 链——软删除旧事件 + 新事件 correction_of 指向旧 event_id；
      旧事件不存在 → NotFoundError。
    - soft_delete：成功；不存在 → NotFoundError。
    - audit=None 时跳过留痕（T009 无 API 层）。

用 ``FakeEventRepository`` 替身（不依赖 DB），符合架构 §5（Protocol + DI，测试注入替身）。
asyncio_mode=auto：async def 测试自动作为 coroutine 运行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from server.app.common.errors import NotFoundError, ValidationError
from server.app.events.domain import (
    ObservationEvent,
    ProcessingStatus,
    Source,
    SyncStatus,
)
from server.app.events.service.idempotency import EventService

NOW = datetime(2026, 8, 11, 0, 0, 0, tzinfo=UTC)
EID = "01HZXKQW7P0QJ9V8R3M4N6H5T2"
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"
FAM = "01HZXKQW7P0QJ9V8R3M4N6H5T4"


@dataclass
class FakeEventRepository:
    """内存仓储替身（实现 domain.ObservationEventRepository）。"""

    events: dict[str, ObservationEvent] = field(default_factory=dict)
    upsert_calls: int = 0

    async def get(self, event_id: str) -> ObservationEvent | None:
        ev = self.events.get(event_id)
        return ev if ev and not ev.is_deleted else None

    async def upsert(self, entity: ObservationEvent) -> ObservationEvent:
        self.upsert_calls += 1
        if entity.event_id in self.events:
            return self.events[entity.event_id]
        self.events[entity.event_id] = entity
        return entity

    async def query(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ObservationEvent]:
        result = [
            ev
            for ev in self.events.values()
            if not ev.is_deleted
            and (baby_id is None or ev.baby_id == baby_id)
            and (family_id is None or ev.family_id == family_id)
            and (event_type is None or ev.event_type == event_type)
        ]
        return sorted(result, key=lambda e: e.start_time, reverse=True)[:limit]

    async def soft_delete(self, event_id: str) -> ObservationEvent | None:
        ev = self.events.get(event_id)
        if ev is None or ev.is_deleted:
            return None
        deleted = ev.model_copy(update={"is_deleted": True})
        self.events[event_id] = deleted
        return deleted


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


@pytest.fixture
def repo() -> FakeEventRepository:
    return FakeEventRepository()


@pytest.fixture
def svc(repo: FakeEventRepository) -> EventService:
    return EventService(repository=repo, clock=FixedClock(NOW))


class TestRecord:
    async def test_record_writes_event(self, svc: EventService, repo: FakeEventRepository):
        ev = await svc.record(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={"amount_ml": 120},
            source=Source.MANUAL,
        )
        assert ev.event_id == EID
        assert ev.server_received_at == NOW  # Clock 填充
        assert ev.sync_status == SyncStatus.PENDING
        assert ev.processing_status == ProcessingStatus.PENDING
        assert repo.upsert_calls == 1
        assert EID in repo.events

    async def test_record_idempotent_same_event_id(
        self, svc: EventService, repo: FakeEventRepository
    ):
        kwargs: dict[str, Any] = dict(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={"amount_ml": 120},
            source=Source.MANUAL,
        )
        first = await svc.record(**kwargs)
        second = await svc.record(**kwargs)
        assert first.event_id == second.event_id == EID
        # 幂等：service 每次都调 upsert（upsert_calls==2），但只存一条。
        assert repo.upsert_calls == 2
        assert len(repo.events) == 1

    @pytest.mark.parametrize(
        "field,value",
        [("event_id", "not-ulid"), ("baby_id", "x"), ("family_id", "x")],
    )
    async def test_record_invalid_ulid_raises(self, svc: EventService, field: str, value: str):
        kwargs: dict[str, Any] = dict(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={"amount_ml": 120},
            source=Source.MANUAL,
        )
        kwargs[field] = value
        with pytest.raises(ValidationError):
            await svc.record(**kwargs)

    async def test_record_system_source(self, svc: EventService):
        ev = await svc.record(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="derived",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={},
            source=Source.SYSTEM,
            user_id=None,
            device_id=None,
        )
        assert ev.source == Source.SYSTEM


class TestCorrect:
    async def test_correct_creates_new_and_soft_deletes_original(
        self, svc: EventService, repo: FakeEventRepository
    ):
        await svc.record(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={"amount_ml": 120},
            source=Source.MANUAL,
        )
        corrected = await svc.correct(
            correction_of=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={"amount_ml": 90},
            source=Source.MANUAL,
        )
        # 新事件 correction_of 指向旧 event_id。
        assert corrected.correction_of == EID
        assert corrected.event_id != EID
        assert corrected.normalized_payload == {"amount_ml": 90}
        # 旧事件被软删除。
        assert repo.events[EID].is_deleted is True
        assert len(repo.events) == 2

    async def test_correct_original_not_found_raises(
        self, svc: EventService, repo: FakeEventRepository
    ):
        with pytest.raises(NotFoundError):
            await svc.correct(
                correction_of="01HZXKQW7P0QJ9V8R3M4N6H5T9",
                baby_id=BABY,
                family_id=FAM,
                event_type="feeding",
                start_time=NOW,
                client_created_at=NOW,
                normalized_payload={},
                source=Source.MANUAL,
            )


class TestSoftDelete:
    async def test_soft_delete_marks_deleted(self, svc: EventService, repo: FakeEventRepository):
        await svc.record(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="diaper",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={},
            source=Source.MANUAL,
        )
        deleted = await svc.soft_delete(event_id=EID)
        assert deleted.is_deleted is True
        assert repo.events[EID].is_deleted is True

    async def test_soft_delete_not_found_raises(self, svc: EventService):
        with pytest.raises(NotFoundError):
            await svc.soft_delete(event_id="01HZXKQW7P0QJ9V8R3M4N6H5T9")


class TestQuery:
    async def test_query_excludes_soft_deleted(self, svc: EventService, repo: FakeEventRepository):
        await svc.record(
            event_id=EID,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload={},
            source=Source.MANUAL,
        )
        await svc.soft_delete(event_id=EID)
        result = await repo.query(baby_id=BABY)
        assert result == []
