# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 20:02:00

"""SQLAlchemy writer/reader for normalized P0 derived tables."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypeAlias

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.events.domain.observation_event import ObservationEvent
from server.app.models import (
    DiaperLog,
    FeedingLog,
    SleepLog,
    SupplementLog,
    TemperatureLog,
)
from server.app.models import (
    ObservationEvent as ORMObservationEvent,
)
from server.app.normalization.service import NormalizedRecord

DerivedModel: TypeAlias = type[FeedingLog | DiaperLog | SleepLog | TemperatureLog | SupplementLog]

_MODEL_BY_RECORD_TYPE: dict[str, DerivedModel] = {
    "feeding": FeedingLog,
    "diaper": DiaperLog,
    "sleep": SleepLog,
    "temperature": TemperatureLog,
    "supplement": SupplementLog,
}
_RECORD_TYPE_BY_MODEL: dict[DerivedModel, str] = {
    model: record_type for record_type, model in _MODEL_BY_RECORD_TYPE.items()
}


def _int_or_none(value: object) -> int | None:
    if not isinstance(value, (float, int, str)):
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _float_or_none(value: object) -> float | None:
    if not isinstance(value, (float, int, str)):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def build_derived_row_values(
    record: NormalizedRecord,
    event: ObservationEvent,
) -> tuple[DerivedModel, dict[str, Any]]:
    """Return ORM model and idempotent row values for a normalized record."""

    model = _MODEL_BY_RECORD_TYPE[record.record_type]
    values: dict[str, Any] = {
        "id": record.id,
        "event_id": record.event_id,
        "baby_id": record.baby_id,
        "family_id": record.family_id,
        "payload": record.payload,
        "is_deleted": record.is_deleted,
    }
    if model is FeedingLog:
        values.update(
            fed_at=event.start_time,
            amount_ml=_int_or_none(record.payload.get("amount_ml")),
            feeding_type=_str_or_none(record.payload.get("feeding_type")),
        )
    elif model is DiaperLog:
        values.update(
            changed_at=event.start_time,
            diaper_type=_str_or_none(record.payload.get("diaper_type")),
        )
    elif model is SleepLog:
        values.update(started_at=event.start_time, ended_at=event.end_time)
    elif model is TemperatureLog:
        values.update(
            measured_at=event.start_time,
            value_c=_float_or_none(record.payload.get("value_c")),
            method=_str_or_none(record.payload.get("method")),
        )
    elif model is SupplementLog:
        values.update(
            supplement_name=_str_or_none(record.payload.get("supplement_name")),
            status=_str_or_none(record.payload.get("status")),
        )
    return model, values


def _row_to_record(
    row: FeedingLog | DiaperLog | SleepLog | TemperatureLog | SupplementLog,
    record_type: str,
    correction_of: str | None,
) -> NormalizedRecord:
    return NormalizedRecord(
        id=row.id,
        event_id=row.event_id,
        baby_id=row.baby_id,
        family_id=row.family_id,
        record_type=record_type,
        payload=row.payload,
        is_deleted=row.is_deleted,
        correction_of=correction_of,
        created_at=row.created_at.isoformat(),
    )


class SQLAlchemyDerivedTableStore:
    """Persist and read normalized P0 records from SQLAlchemy derived tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        record: NormalizedRecord,
        event: ObservationEvent,
    ) -> NormalizedRecord:
        model, values = build_derived_row_values(record, event)
        update_values = {key: value for key, value in values.items() if key != "id"}
        update_values["updated_at"] = utc_now()
        stmt = pg_insert(model).values(**values).on_conflict_do_update(
            index_elements=[model.event_id],
            set_=update_values,
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return record

    async def list_by_baby(
        self,
        baby_id: str,
        *,
        include_deleted: bool = False,
    ) -> list[NormalizedRecord]:
        records: list[NormalizedRecord] = []
        for model, record_type in _RECORD_TYPE_BY_MODEL.items():
            stmt = (
                select(model, ORMObservationEvent.correction_of)
                .join(ORMObservationEvent, model.event_id == ORMObservationEvent.event_id)
                .where(model.baby_id == baby_id)
            )
            if not include_deleted:
                stmt = stmt.where(model.is_deleted.is_(False))
            rows = await self.session.execute(stmt.order_by(model.created_at.asc()))
            records.extend(
                _row_to_record(row, record_type, correction_of)
                for row, correction_of in rows
            )
        return records

    async def latest_start_time(self, baby_id: str) -> datetime | None:
        """Return newest derived row time for diagnostics/tests."""

        rows = await self.list_by_baby(baby_id)
        latest: datetime | None = None
        for row in rows:
            parsed = datetime.fromisoformat(row.created_at)
            latest = parsed if latest is None or parsed > latest else latest
        return latest
