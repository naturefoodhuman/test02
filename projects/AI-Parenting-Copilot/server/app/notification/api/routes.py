# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:55:00


"""Alert API routes for dev/in-memory mode."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import AppError
from server.app.notification.alert_repo import (
    AckAlertRequest,
    AlertRecord,
    CreateAlertRequest,
    FeedbackRequest,
    InMemoryAlertRepository,
)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


def _repo(request: Request) -> InMemoryAlertRepository:
    repo = getattr(request.app.state, "alert_repository", None)
    if repo is None:
        raise AppError(
            "Alert repository is not configured",
            code="ALERT_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(InMemoryAlertRepository, repo)


@router.post("", response_model=AlertRecord)
async def create_alert(payload: CreateAlertRequest, request: Request) -> AlertRecord:
    return await _repo(request).create(payload)


@router.get("", response_model=list[AlertRecord])
async def list_alerts(request: Request, family_id: str | None = None) -> list[AlertRecord]:
    return await _repo(request).list_active(family_id=family_id)


@router.get("/{alert_id}", response_model=AlertRecord)
async def get_alert(alert_id: str, request: Request) -> AlertRecord:
    return await _repo(request).get(alert_id)


@router.post("/{alert_id}/ack", response_model=AlertRecord)
async def ack_alert(alert_id: str, payload: AckAlertRequest, request: Request) -> AlertRecord:
    return await _repo(request).ack(alert_id, payload)


@router.post("/{alert_id}/feedback", response_model=AlertRecord)
async def feedback_alert(
    alert_id: str,
    payload: FeedbackRequest,
    request: Request,
) -> AlertRecord:
    return await _repo(request).feedback(alert_id, payload)
