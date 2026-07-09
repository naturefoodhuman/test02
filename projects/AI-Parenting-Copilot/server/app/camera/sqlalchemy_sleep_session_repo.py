# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 16:05:00


"""SQLAlchemy SleepSession repository adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.camera.sleep_session import SleepSessionRecord, SleepSessionState
from server.app.common.errors import NotFoundError
from server.app.models import SleepSession as ORMSleepSession


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class SQLAlchemySleepSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        row = await self.session.scalar(
            select(ORMSleepSession).where(ORMSleepSession.id == session_id)
        )
        if row is None:
            raise NotFoundError("Sleep session not found", evidence={"session_id": session_id})
        return SleepSessionRecord(
            id=row.id,
            baby_id=row.baby_id,
            family_id=row.family_id,
            state=SleepSessionState(row.state),
            started_at=row.started_at.isoformat() if row.started_at else "",
            ended_at=row.ended_at.isoformat() if row.ended_at else None,
            roi_config=row.roi_config,
        )
