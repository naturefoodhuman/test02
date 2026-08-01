# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 13:25:00

"""SQLAlchemy SensorEvent repository for mmWave telemetry."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.ids import new_ulid
from server.app.mmwave.sensor_event_mapper import SensorEventCandidate
from server.app.models import SensorEvent as ORMSensorEvent


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class SensorEventRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    device_id: str
    ts: str
    signal_type: str
    payload: dict[str, object] = Field(default_factory=dict)


class SQLAlchemySensorEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, record: SensorEventRecord | SensorEventCandidate) -> SensorEventRecord:
        if isinstance(record, SensorEventCandidate):
            domain = SensorEventRecord(
                device_id=record.device_id,
                ts=record.ts,
                signal_type=record.signal_type,
                payload=record.payload,
            )
        else:
            domain = record
        self.session.add(
            ORMSensorEvent(
                id=domain.id,
                device_id=domain.device_id,
                ts=_parse_datetime(domain.ts),
                signal_type=domain.signal_type,
                payload=domain.payload,
            )
        )
        await self.session.flush()
        return domain

    async def list_by_device(self, device_id: str, *, limit: int = 100) -> list[SensorEventRecord]:
        rows = await self.session.scalars(
            select(ORMSensorEvent)
            .where(ORMSensorEvent.device_id == device_id)
            .order_by(ORMSensorEvent.ts.desc())
            .limit(limit)
        )
        return [
            SensorEventRecord(
                id=row.id,
                device_id=row.device_id,
                ts=row.ts.isoformat(),
                signal_type=row.signal_type,
                payload=row.payload,
            )
            for row in rows
        ]
