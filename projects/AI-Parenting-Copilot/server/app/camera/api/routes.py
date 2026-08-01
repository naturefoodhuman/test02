# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:08:00

"""Camera and sleep session API routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from server.app.camera.roi import ROIConfig
from server.app.camera.rtsp_client import MockRTSPSnapshotClient
from server.app.camera.sleep_session import InMemorySleepSessionRepository, SleepSessionRecord
from server.app.camera.sqlalchemy_camera_event_repo import (
    CameraEventRecord,
    SQLAlchemyCameraEventRepository,
)
from server.app.camera.sqlalchemy_sleep_session_repo import SQLAlchemySleepSessionRepository
from server.app.common.clock import utc_now
from server.app.common.errors import AppError
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1", tags=["camera"])


class StartSleepSessionRequest(BaseModel):
    baby_id: str
    family_id: str


class CreateCameraEventRequest(BaseModel):
    camera_id: str
    session_id: str | None = None
    ts: str = Field(default_factory=lambda: utc_now().isoformat())
    kind: str
    confidence: float | None = None
    clip_path: str | None = None


def _repo(request: Request) -> InMemorySleepSessionRepository | SQLAlchemySleepSessionRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemySleepSessionRepository(db_session)
    repo = getattr(request.app.state, "sleep_session_repository", None)
    if repo is None:
        raise AppError(
            "Sleep session repository is not configured",
            code="SLEEP_SESSION_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(InMemorySleepSessionRepository, repo)


def _dev_camera_events(request: Request) -> list[CameraEventRecord]:
    records = getattr(request.app.state, "camera_event_records", None)
    if records is None:
        records = []
        request.app.state.camera_event_records = records
    return cast(list[CameraEventRecord], records)


@router.post("/sleep-sessions", response_model=SleepSessionRecord)
async def start_sleep_session(
    payload: StartSleepSessionRequest,
    request: Request,
) -> SleepSessionRecord:
    session = await _repo(request).start(baby_id=payload.baby_id, family_id=payload.family_id)
    await record_request_audit(
        request,
        action="sleep_session.start",
        resource=f"sleep_session:{session.id}",
        after=session.model_dump(mode="json"),
        db_only=True,
    )
    return session


@router.post("/sleep-sessions/{session_id}/pause", response_model=SleepSessionRecord)
async def pause_sleep_session(session_id: str, request: Request) -> SleepSessionRecord:
    session = await _repo(request).pause(session_id)
    await record_request_audit(
        request,
        action="sleep_session.pause",
        resource=f"sleep_session:{session_id}",
        after=session.model_dump(mode="json"),
        db_only=True,
    )
    return session


@router.post("/sleep-sessions/{session_id}/resume", response_model=SleepSessionRecord)
async def resume_sleep_session(session_id: str, request: Request) -> SleepSessionRecord:
    session = await _repo(request).resume(session_id)
    await record_request_audit(
        request,
        action="sleep_session.resume",
        resource=f"sleep_session:{session_id}",
        after=session.model_dump(mode="json"),
        db_only=True,
    )
    return session


@router.post("/sleep-sessions/{session_id}/end", response_model=SleepSessionRecord)
async def end_sleep_session(session_id: str, request: Request) -> SleepSessionRecord:
    session = await _repo(request).end(session_id)
    await record_request_audit(
        request,
        action="sleep_session.end",
        resource=f"sleep_session:{session_id}",
        after=session.model_dump(mode="json"),
        db_only=True,
    )
    return session


@router.put("/sleep-sessions/{session_id}/roi", response_model=SleepSessionRecord)
async def set_roi(session_id: str, payload: ROIConfig, request: Request) -> SleepSessionRecord:
    session = await _repo(request).set_roi(session_id, payload)
    await record_request_audit(
        request,
        action="sleep_session.roi_update",
        resource=f"sleep_session:{session_id}",
        after=session.model_dump(mode="json"),
        db_only=True,
    )
    return session


@router.post("/camera-events", response_model=CameraEventRecord)
async def create_camera_event(
    payload: CreateCameraEventRequest,
    request: Request,
) -> CameraEventRecord:
    record = CameraEventRecord(**payload.model_dump())
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        record = await SQLAlchemyCameraEventRepository(db_session).add(record)
    else:
        _dev_camera_events(request).append(record)
    await record_request_audit(
        request,
        action="camera_event.create",
        resource=f"camera_event:{record.id}",
        after=record.model_dump(mode="json"),
        db_only=True,
    )
    return record


@router.get("/sleep-sessions/{session_id}/camera-events", response_model=list[CameraEventRecord])
async def list_camera_events_by_session(
    session_id: str,
    request: Request,
) -> list[CameraEventRecord]:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return await SQLAlchemyCameraEventRepository(db_session).list_by_session(session_id)
    return [record for record in _dev_camera_events(request) if record.session_id == session_id]


@router.get("/cameras/{camera_id}/snapshot")
async def camera_snapshot(camera_id: str) -> Response:
    snapshot = await MockRTSPSnapshotClient(camera_id).snapshot()
    return Response(content=snapshot, media_type="image/png")
