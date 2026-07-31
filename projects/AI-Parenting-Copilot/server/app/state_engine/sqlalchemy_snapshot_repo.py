# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 16:05:00


"""SQLAlchemy DerivedBabyState snapshot repository."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.models import DerivedBabyState as ORMDerivedBabyState
from server.app.state_engine.snapshot_repo import DerivedBabyStateSnapshot


def _parse_computed_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    except ValueError:
        return utc_now()


class SQLAlchemyStateSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, snapshot: DerivedBabyStateSnapshot) -> DerivedBabyStateSnapshot:
        computed_at = _parse_computed_at(snapshot.computed_at)
        stmt = pg_insert(ORMDerivedBabyState).values(
            baby_id=snapshot.baby_id,
            family_id=snapshot.family_id,
            snapshot=snapshot.snapshot,
            computed_at=computed_at,
        ).on_conflict_do_update(
            index_elements=[ORMDerivedBabyState.baby_id],
            set_={
                "family_id": snapshot.family_id,
                "snapshot": snapshot.snapshot,
                "computed_at": computed_at,
                "updated_at": utc_now(),
            },
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return snapshot

    async def get(self, baby_id: str) -> DerivedBabyStateSnapshot | None:
        row = await self.session.scalar(
            select(ORMDerivedBabyState).where(ORMDerivedBabyState.baby_id == baby_id)
        )
        if row is None:
            return None
        return DerivedBabyStateSnapshot(
            baby_id=row.baby_id,
            family_id=row.family_id,
            snapshot=row.snapshot,
            computed_at=row.computed_at.isoformat(),
            source_event_count=int(row.snapshot.get("source_event_count", 0) or 0),
        )
