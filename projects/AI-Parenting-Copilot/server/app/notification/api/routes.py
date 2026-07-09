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
from server.app.notification.sqlalchemy_alert_repo import SQLAlchemyAlertRepository
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


def _repo(request: Request) -> InMemoryAlertRepository | SQLAlchemyAlertRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemyAlertRepository(db_session)
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
    alert = await _repo(request).create(payload)
    await record_request_audit(
        request,
        action="alert.create",
        resource=f"alert:{alert.id}",
        after=alert.model_dump(mode="json"),
        db_only=True,
    )
    return alert


@router.get("", response_model=list[AlertRecord])
async def list_alerts(request: Request, family_id: str | None = None) -> list[AlertRecord]:
    return await _repo(request).list_active(family_id=family_id)


@router.get("/{alert_id}", response_model=AlertRecord)
async def get_alert(alert_id: str, request: Request) -> AlertRecord:
    return await _repo(request).get(alert_id)


@router.post("/{alert_id}/ack", response_model=AlertRecord)
async def ack_alert(alert_id: str, payload: AckAlertRequest, request: Request) -> AlertRecord:
    alert = await _repo(request).ack(alert_id, payload)
    await record_request_audit(
        request,
        action="alert.ack",
        resource=f"alert:{alert_id}",
        after=alert.model_dump(mode="json"),
        db_only=True,
    )
    return alert


@router.post("/{alert_id}/feedback", response_model=AlertRecord)
async def feedback_alert(
    alert_id: str,
    payload: FeedbackRequest,
    request: Request,
) -> AlertRecord:
    alert = await _repo(request).feedback(alert_id, payload)
    await record_request_audit(
        request,
        action="alert.feedback",
        resource=f"alert:{alert_id}",
        after=alert.model_dump(mode="json"),
        db_only=True,
    )
    return alert
