# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 15:20:00


"""SQLAlchemy EventRepository implementation."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.common.errors import NotFoundError
from server.app.events.domain.observation_event import (
    EventCorrectionRequest,
    EventSource,
    ObservationEvent,
    ObservationEventCreate,
    ProcessingStatus,
    SyncStatus,
)
from server.app.events.service.idempotency import ensure_idempotent
from server.app.models import ObservationEvent as ORMObservationEvent


class SQLAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, event: ObservationEventCreate) -> ObservationEvent:
        row = await self.session.scalar(
            select(ORMObservationEvent).where(ORMObservationEvent.event_id == event.event_id)
        )
        existing = self._to_domain(row) if row is not None else None
        ensure_idempotent(existing, event)
        if row is not None and existing is not None:
            return existing
        row = ORMObservationEvent(
            event_id=event.event_id,
            baby_id=event.baby_id,
            family_id=event.family_id,
            user_id=event.user_id,
            device_id=event.device_id,
            event_type=event.event_type,
            start_time=event.start_time,
            end_time=event.end_time,
            client_created_at=event.client_created_at,
            raw_input=event.raw_input,
            normalized_payload=event.normalized_payload or event.payload,
            confidence=event.confidence,
            source=str(event.source),
            attachments=event.attachments,
            correction_of=event.correction_of,
            is_deleted=event.is_deleted,
        )
        self.session.add(row)
        await self.session.flush()
        return self._to_domain(row)

    async def get(self, event_id: str) -> ObservationEvent | None:
        row = await self.session.scalar(
            select(ORMObservationEvent).where(ORMObservationEvent.event_id == event_id)
        )
        return self._to_domain(row) if row is not None else None

    async def list_by_baby(
        self,
        baby_id: str,
        *,
        include_deleted: bool = False,
    ) -> list[ObservationEvent]:
        stmt = select(ORMObservationEvent).where(ORMObservationEvent.baby_id == baby_id)
        if not include_deleted:
            stmt = stmt.where(ORMObservationEvent.is_deleted.is_(False))
        rows = await self.session.scalars(stmt.order_by(ORMObservationEvent.start_time.desc()))
        return [self._to_domain(row) for row in rows]

    async def soft_delete(self, event_id: str) -> ObservationEvent:
        row = await self.session.scalar(
            select(ORMObservationEvent).where(ORMObservationEvent.event_id == event_id)
        )
        if row is None:
            raise NotFoundError("Event not found", evidence={"event_id": event_id})
        row.is_deleted = True
        row.updated_at = utc_now()
        await self.session.flush()
        return self._to_domain(row)

    async def correct(self, event_id: str, correction: EventCorrectionRequest) -> ObservationEvent:
        original = await self.get(event_id)
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
            raw_input=correction.raw_input,
            normalized_payload=correction.normalized_payload,
            payload=correction.normalized_payload,
            confidence=original.confidence,
            source=original.source,
            attachments=original.attachments,
            correction_of=original.event_id,
        )
        return await self.upsert(corrected)

    @staticmethod
    def _to_domain(row: ORMObservationEvent) -> ObservationEvent:
        return ObservationEvent(
            event_id=row.event_id,
            baby_id=row.baby_id,
            family_id=row.family_id,
            user_id=row.user_id,
            device_id=row.device_id,
            event_type=row.event_type,
            start_time=row.start_time,
            end_time=row.end_time,
            client_created_at=row.client_created_at,
            server_received_at=row.server_received_at,
            raw_input=row.raw_input,
            normalized_payload=row.normalized_payload,
            payload=row.normalized_payload,
            confidence=row.confidence,
            source=EventSource(row.source),
            attachments=row.attachments,
            correction_of=row.correction_of,
            is_deleted=row.is_deleted,
            sync_status=SyncStatus(row.sync_status),
            processing_status=ProcessingStatus(row.processing_status),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
