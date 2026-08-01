# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 13:26:00

"""SQLAlchemy CameraEvent repository for shadow-mode camera events."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.ids import new_ulid
from server.app.models import CameraEvent as ORMCameraEvent


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class CameraEventRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    camera_id: str
    session_id: str | None = None
    ts: str
    kind: str
    confidence: float | None = None
    clip_path: str | None = None


class SQLAlchemyCameraEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, record: CameraEventRecord) -> CameraEventRecord:
        self.session.add(
            ORMCameraEvent(
                id=record.id,
                camera_id=record.camera_id,
                session_id=record.session_id,
                ts=_parse_datetime(record.ts),
                kind=record.kind,
                confidence=record.confidence,
                clip_path=record.clip_path,
            )
        )
        await self.session.flush()
        return record

    async def list_by_session(
        self,
        session_id: str,
        *,
        limit: int = 100,
    ) -> list[CameraEventRecord]:
        rows = await self.session.scalars(
            select(ORMCameraEvent)
            .where(ORMCameraEvent.session_id == session_id)
            .order_by(ORMCameraEvent.ts.desc())
            .limit(limit)
        )
        return [self._to_record(row) for row in rows]

    async def list_by_camera(self, camera_id: str, *, limit: int = 100) -> list[CameraEventRecord]:
        rows = await self.session.scalars(
            select(ORMCameraEvent)
            .where(ORMCameraEvent.camera_id == camera_id)
            .order_by(ORMCameraEvent.ts.desc())
            .limit(limit)
        )
        return [self._to_record(row) for row in rows]

    @staticmethod
    def _to_record(row: ORMCameraEvent) -> CameraEventRecord:
        return CameraEventRecord(
            id=row.id,
            camera_id=row.camera_id,
            session_id=row.session_id,
            ts=row.ts.isoformat(),
            kind=row.kind,
            confidence=row.confidence,
            clip_path=row.clip_path,
        )
