# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 21:05:00

"""SyncState domain records and repositories."""

from __future__ import annotations

from pydantic import BaseModel

from server.app.common.clock import utc_now
from server.app.common.errors import NotFoundError


class SyncStateRecord(BaseModel):
    client_id: str
    family_id: str | None = None
    last_seen_at: str
    pending_count: int = 0


class SyncHeartbeatRequest(BaseModel):
    client_id: str
    family_id: str | None = None
    pending_count: int = 0


class InMemorySyncStateRepository:
    def __init__(self) -> None:
        self.records: dict[str, SyncStateRecord] = {}

    async def heartbeat(self, request: SyncHeartbeatRequest) -> SyncStateRecord:
        record = SyncStateRecord(
            client_id=request.client_id,
            family_id=request.family_id,
            pending_count=request.pending_count,
            last_seen_at=utc_now().isoformat(),
        )
        self.records[record.client_id] = record
        return record

    async def get(self, client_id: str) -> SyncStateRecord:
        record = self.records.get(client_id)
        if record is None:
            raise NotFoundError("Sync state not found", evidence={"client_id": client_id})
        return record
