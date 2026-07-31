# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 20:05:00

"""PostgreSQL-backed normalization/state worker primitives."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import asyncpg  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from server.app.common.clock import utc_now
from server.app.common.event_bus import parse_pg_notify_payload
from server.app.db import normalize_database_url
from server.app.events.domain.observation_event import ProcessingStatus
from server.app.events.infra.sqlalchemy_repository import SQLAlchemyEventRepository
from server.app.models import ObservationEvent as ORMObservationEvent
from server.app.normalization.service import NormalizationService
from server.app.normalization.sqlalchemy_store import SQLAlchemyDerivedTableStore
from server.app.state_engine.engine import BabyStateEngine
from server.app.state_engine.sqlalchemy_snapshot_repo import SQLAlchemyStateSnapshotRepository


@dataclass(frozen=True)
class ProcessedEventResult:
    event_id: str
    baby_id: str
    family_id: str
    record_type: str | None


def to_asyncpg_url(database_url: str) -> str:
    """Convert SQLAlchemy asyncpg URLs to URLs accepted by asyncpg.connect."""

    return normalize_database_url(database_url).replace("postgresql+asyncpg://", "postgresql://", 1)


class PendingEventProcessor:
    """Drain pending observation events into derived tables and baby state."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.derived_store = SQLAlchemyDerivedTableStore(session)
        self.snapshot_repo = SQLAlchemyStateSnapshotRepository(session)

    async def process_pending(self, *, limit: int = 100) -> list[ProcessedEventResult]:
        rows = await self.session.scalars(
            select(ORMObservationEvent)
            .where(
                ORMObservationEvent.processing_status == ProcessingStatus.PENDING.value,
                ORMObservationEvent.is_deleted.is_(False),
            )
            .order_by(ORMObservationEvent.client_created_at.asc())
            .limit(limit)
        )
        touched_babies: dict[str, str] = {}
        results: list[ProcessedEventResult] = []
        for row in rows:
            event = SQLAlchemyEventRepository._to_domain(row)
            record = NormalizationService().normalize(event)
            if record is not None:
                await self.derived_store.upsert(record, event)
                touched_babies[event.baby_id] = event.family_id
            row.processing_status = event.processing_status.value
            row.updated_at = utc_now()
            results.append(
                ProcessedEventResult(
                    event_id=event.event_id,
                    baby_id=event.baby_id,
                    family_id=event.family_id,
                    record_type=record.record_type if record is not None else None,
                )
            )
        for baby_id, family_id in touched_babies.items():
            records = await self.derived_store.list_by_baby(baby_id)
            snapshot = BabyStateEngine().recompute(
                baby_id=baby_id,
                family_id=family_id,
                records=records,
            )
            await self.snapshot_repo.upsert(snapshot)
        await self.session.flush()
        return results


async def process_pending_events(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    limit: int = 100,
) -> list[ProcessedEventResult]:
    """Run one transactional pending-event drain."""

    async with session_factory() as session:
        async with session.begin():
            return await PendingEventProcessor(session).process_pending(limit=limit)


class PostgresEventNormalizationWorker:
    """LISTEN/NOTIFY worker that drains pending events after DB commits."""

    name = "postgres-event-normalization-worker"

    def __init__(
        self,
        *,
        database_url: str,
        session_factory: async_sessionmaker[AsyncSession],
        channel: str = "events.changed",
        process_limit: int = 100,
        processor: Callable[..., Awaitable[list[ProcessedEventResult]]] = process_pending_events,
    ) -> None:
        self.database_url = database_url
        self.session_factory = session_factory
        self.channel = channel
        self.process_limit = process_limit
        self.processor = processor
        self._connection: asyncpg.Connection | None = None
        self._tasks: set[asyncio.Task[Any]] = set()
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._connection = await asyncpg.connect(to_asyncpg_url(self.database_url))
        await self._connection.add_listener(self.channel, self._on_notify)
        await self._run_once()

    async def stop(self) -> None:
        if self._connection is not None:
            await self._connection.remove_listener(self.channel, self._on_notify)
            await self._connection.close()
            self._connection = None
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    def _on_notify(
        self,
        _connection: asyncpg.Connection,
        _pid: int,
        _channel: str,
        payload: str,
    ) -> None:
        try:
            parse_pg_notify_payload(payload)
        except (KeyError, TypeError, ValueError):
            return
        task = asyncio.create_task(self._run_once())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_once(self) -> list[ProcessedEventResult]:
        async with self._lock:
            return await self.processor(
                self.session_factory,
                limit=self.process_limit,
            )
