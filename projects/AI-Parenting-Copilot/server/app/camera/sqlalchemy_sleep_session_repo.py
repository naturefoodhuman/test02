# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:05:00

"""SQLAlchemy SleepSession repository adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.camera.roi import ROIConfig
from server.app.camera.sleep_session import SleepSessionRecord, SleepSessionState
from server.app.common.clock import utc_now
from server.app.common.errors import ConflictError, NotFoundError
from server.app.models import SleepSession as ORMSleepSession


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class SQLAlchemySleepSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start(self, *, baby_id: str, family_id: str) -> SleepSessionRecord:
        return await self.add(SleepSessionRecord(baby_id=baby_id, family_id=family_id))

    async def add(self, record: SleepSessionRecord) -> SleepSessionRecord:
        self.session.add(
            ORMSleepSession(
                id=record.id,
                baby_id=record.baby_id,
                family_id=record.family_id,
                state=record.state.value,
                started_at=_parse_datetime(record.started_at),
                ended_at=_parse_datetime(record.ended_at),
                roi_config=record.roi_config,
            )
        )
        await self.session.flush()
        return record

    async def get(self, session_id: str) -> SleepSessionRecord:
        return self._to_domain(await self._row(session_id))

    async def pause(self, session_id: str) -> SleepSessionRecord:
        row = await self._row(session_id)
        if row.state != SleepSessionState.ACTIVE.value:
            raise ConflictError("Only active sleep sessions can be paused")
        row.state = SleepSessionState.PAUSED.value
        row.updated_at = utc_now()
        await self.session.flush()
        return self._to_domain(row)

    async def resume(self, session_id: str) -> SleepSessionRecord:
        row = await self._row(session_id)
        if row.state != SleepSessionState.PAUSED.value:
            raise ConflictError("Only paused sleep sessions can be resumed")
        row.state = SleepSessionState.ACTIVE.value
        row.updated_at = utc_now()
        await self.session.flush()
        return self._to_domain(row)

    async def end(self, session_id: str) -> SleepSessionRecord:
        row = await self._row(session_id)
        if row.state == SleepSessionState.ENDED.value:
            raise ConflictError("Sleep session is already ended")
        row.state = SleepSessionState.ENDED.value
        row.ended_at = utc_now()
        row.updated_at = row.ended_at
        await self.session.flush()
        return self._to_domain(row)

    async def set_roi(self, session_id: str, roi: ROIConfig) -> SleepSessionRecord:
        row = await self._row(session_id)
        row.roi_config = roi.as_dict()
        row.updated_at = utc_now()
        await self.session.flush()
        return self._to_domain(row)

    async def _row(self, session_id: str) -> ORMSleepSession:
        row = await self.session.scalar(
            select(ORMSleepSession).where(ORMSleepSession.id == session_id)
        )
        if row is None:
            raise NotFoundError("Sleep session not found", evidence={"session_id": session_id})
        return row

    @staticmethod
    def _to_domain(row: ORMSleepSession) -> SleepSessionRecord:
        return SleepSessionRecord(
            id=row.id,
            baby_id=row.baby_id,
            family_id=row.family_id,
            state=SleepSessionState(row.state),
            started_at=row.started_at.isoformat() if row.started_at else "",
            ended_at=row.ended_at.isoformat() if row.ended_at else None,
            roi_config=row.roi_config,
        )
