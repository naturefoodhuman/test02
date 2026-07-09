# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""State Engine API routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import NotFoundError
from server.app.state_engine.snapshot_repo import (
    DerivedBabyStateSnapshot,
    InMemoryStateSnapshotRepository,
)
from server.app.state_engine.sqlalchemy_snapshot_repo import SQLAlchemyStateSnapshotRepository

router = APIRouter(prefix="/api/v1/babies", tags=["state"])


@router.get("/{baby_id}/state", response_model=DerivedBabyStateSnapshot)
async def get_baby_state(baby_id: str, request: Request) -> DerivedBabyStateSnapshot:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        snapshot = await SQLAlchemyStateSnapshotRepository(db_session).get(baby_id)
    else:
        repo = cast(InMemoryStateSnapshotRepository, request.app.state.state_snapshot_repository)
        snapshot = repo.get(baby_id)
    if snapshot is None:
        raise NotFoundError("DerivedBabyState not found", evidence={"baby_id": baby_id})
    return snapshot
