# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 21:06:00

"""SQLAlchemy SyncState repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.common.errors import NotFoundError
from server.app.models import SyncState as ORMSyncState
from server.app.sync.state_repo import SyncHeartbeatRequest, SyncStateRecord


class SQLAlchemySyncStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def heartbeat(self, request: SyncHeartbeatRequest) -> SyncStateRecord:
        last_seen_at = utc_now()
        stmt = pg_insert(ORMSyncState).values(
            client_id=request.client_id,
            family_id=request.family_id,
            pending_count=request.pending_count,
            last_seen_at=last_seen_at,
        ).on_conflict_do_update(
            index_elements=[ORMSyncState.client_id],
            set_={
                "family_id": request.family_id,
                "pending_count": request.pending_count,
                "last_seen_at": last_seen_at,
                "updated_at": last_seen_at,
            },
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return SyncStateRecord(
            client_id=request.client_id,
            family_id=request.family_id,
            pending_count=request.pending_count,
            last_seen_at=last_seen_at.isoformat(),
        )

    async def get(self, client_id: str) -> SyncStateRecord:
        row = await self.session.scalar(
            select(ORMSyncState).where(ORMSyncState.client_id == client_id)
        )
        if row is None:
            raise NotFoundError("Sync state not found", evidence={"client_id": client_id})
        return SyncStateRecord(
            client_id=row.client_id,
            family_id=row.family_id,
            pending_count=row.pending_count,
            last_seen_at=row.last_seen_at.isoformat() if row.last_seen_at else "",
        )
