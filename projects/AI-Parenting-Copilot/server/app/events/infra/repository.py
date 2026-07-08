# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:05:00


"""ObservationEvent repository protocol and in-memory implementation."""

from __future__ import annotations

from typing import Protocol

from server.app.common.clock import utc_now
from server.app.common.errors import NotFoundError
from server.app.events.domain.observation_event import (
    EventCorrectionRequest,
    ObservationEvent,
    ObservationEventCreate,
    ProcessingStatus,
    SyncStatus,
)
from server.app.events.service.idempotency import ensure_idempotent


class EventRepository(Protocol):
    async def upsert(self, event: ObservationEventCreate) -> ObservationEvent: ...
    async def get(self, event_id: str) -> ObservationEvent | None: ...
    async def list_by_baby(
        self,
        baby_id: str,
        *,
        include_deleted: bool = False,
    ) -> list[ObservationEvent]: ...
    async def soft_delete(self, event_id: str) -> ObservationEvent: ...
    async def correct(
        self,
        event_id: str,
        correction: EventCorrectionRequest,
    ) -> ObservationEvent: ...


class InMemoryEventRepository:
    """Deterministic in-memory Event Store for dev/tests before DB repository lands."""

    def __init__(self) -> None:
        self.events: dict[str, ObservationEvent] = {}

    async def upsert(self, event: ObservationEventCreate) -> ObservationEvent:
        existing = self.events.get(event.event_id)
        ensure_idempotent(existing, event)
        if existing is not None:
            return existing
        persisted = ObservationEvent.model_validate(event.model_dump())
        persisted.sync_status = SyncStatus.PENDING
        persisted.processing_status = ProcessingStatus.PENDING
        self.events[persisted.event_id] = persisted
        return persisted

    async def get(self, event_id: str) -> ObservationEvent | None:
        return self.events.get(event_id)

    async def list_by_baby(
        self,
        baby_id: str,
        *,
        include_deleted: bool = False,
    ) -> list[ObservationEvent]:
        rows = [event for event in self.events.values() if event.baby_id == baby_id]
        if not include_deleted:
            rows = [event for event in rows if not event.is_deleted]
        return sorted(rows, key=lambda event: event.start_time, reverse=True)

    async def soft_delete(self, event_id: str) -> ObservationEvent:
        event = self.events.get(event_id)
        if event is None:
            raise NotFoundError("Event not found", evidence={"event_id": event_id})
        event.is_deleted = True
        event.updated_at = utc_now()
        return event

    async def correct(self, event_id: str, correction: EventCorrectionRequest) -> ObservationEvent:
        original = self.events.get(event_id)
        if original is None:
            raise NotFoundError("Event not found", evidence={"event_id": event_id})
        corrected = ObservationEventCreate(
            baby_id=original.baby_id,
            family_id=original.family_id,
            user_id=original.user_id,
            device_id=original.device_id,
            event_type=original.event_type,
            start_time=original.start_time,
            end_time=original.end_time,
            client_created_at=correction.client_created_at,
            raw_input=correction.raw_input or {"correction_reason": correction.reason},
            normalized_payload=correction.normalized_payload,
            payload=correction.normalized_payload,
            confidence=original.confidence,
            source=original.source,
            attachments=original.attachments,
            correction_of=original.event_id,
        )
        return await self.upsert(corrected)
