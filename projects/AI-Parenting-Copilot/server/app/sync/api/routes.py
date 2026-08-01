# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 21:07:00

"""Sync state API routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import AppError
from server.app.observability.request_audit import record_request_audit
from server.app.sync.sqlalchemy_state_repo import SQLAlchemySyncStateRepository
from server.app.sync.state_repo import (
    InMemorySyncStateRepository,
    SyncHeartbeatRequest,
    SyncStateRecord,
)

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


def _repo(request: Request) -> InMemorySyncStateRepository | SQLAlchemySyncStateRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemySyncStateRepository(db_session)
    repo = getattr(request.app.state, "sync_state_repository", None)
    if repo is None:
        raise AppError("Sync state repository is not configured", code="SYNC_REPO_UNAVAILABLE")
    return cast(InMemorySyncStateRepository, repo)


@router.post("/heartbeat", response_model=SyncStateRecord)
async def sync_heartbeat(payload: SyncHeartbeatRequest, request: Request) -> SyncStateRecord:
    record = await _repo(request).heartbeat(payload)
    await record_request_audit(
        request,
        action="sync.heartbeat",
        resource=f"sync_state:{record.client_id}",
        after=record.model_dump(mode="json"),
    )
    return record


@router.get("/state/{client_id}", response_model=SyncStateRecord)
async def get_sync_state(client_id: str, request: Request) -> SyncStateRecord:
    return await _repo(request).get(client_id)
