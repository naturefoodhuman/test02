# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 07:15:00


"""Camera and sleep session API routes for dev mode."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from server.app.camera.roi import ROIConfig
from server.app.camera.rtsp_client import MockRTSPSnapshotClient
from server.app.camera.sleep_session import InMemorySleepSessionRepository, SleepSessionRecord
from server.app.common.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["camera"])


class StartSleepSessionRequest(BaseModel):
    baby_id: str
    family_id: str


def _repo(request: Request) -> InMemorySleepSessionRepository:
    repo = getattr(request.app.state, "sleep_session_repository", None)
    if repo is None:
        raise AppError(
            "Sleep session repository is not configured",
            code="SLEEP_SESSION_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(InMemorySleepSessionRepository, repo)


@router.post("/sleep-sessions", response_model=SleepSessionRecord)
async def start_sleep_session(
    payload: StartSleepSessionRequest,
    request: Request,
) -> SleepSessionRecord:
    return await _repo(request).start(baby_id=payload.baby_id, family_id=payload.family_id)


@router.post("/sleep-sessions/{session_id}/pause", response_model=SleepSessionRecord)
async def pause_sleep_session(session_id: str, request: Request) -> SleepSessionRecord:
    return await _repo(request).pause(session_id)


@router.post("/sleep-sessions/{session_id}/resume", response_model=SleepSessionRecord)
async def resume_sleep_session(session_id: str, request: Request) -> SleepSessionRecord:
    return await _repo(request).resume(session_id)


@router.post("/sleep-sessions/{session_id}/end", response_model=SleepSessionRecord)
async def end_sleep_session(session_id: str, request: Request) -> SleepSessionRecord:
    return await _repo(request).end(session_id)


@router.put("/sleep-sessions/{session_id}/roi", response_model=SleepSessionRecord)
async def set_roi(session_id: str, payload: ROIConfig, request: Request) -> SleepSessionRecord:
    return await _repo(request).set_roi(session_id, payload)


@router.get("/cameras/{camera_id}/snapshot")
async def camera_snapshot(camera_id: str) -> Response:
    snapshot = await MockRTSPSnapshotClient(camera_id).snapshot()
    return Response(content=snapshot, media_type="image/png")
