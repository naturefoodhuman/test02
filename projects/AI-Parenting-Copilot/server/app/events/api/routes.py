# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:05:00


"""ObservationEvent API routes for dev/in-memory mode."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Query, Request

from server.app.common.errors import AppError, NotFoundError
from server.app.events.domain.observation_event import (
    EventCorrectionRequest,
    ObservationEvent,
    ObservationEventCreate,
)
from server.app.events.infra.repository import EventRepository
from server.app.observability.audit import AuditActor, AuditRecord, AuditSink

router = APIRouter(prefix="/api/v1/events", tags=["events"])


def _event_repo(request: Request) -> EventRepository:
    repo = getattr(request.app.state, "event_repository", None)
    if repo is None:
        raise AppError(
            "Event repository is not configured",
            code="EVENT_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(EventRepository, repo)


def _audit_sink(request: Request) -> AuditSink | None:
    return getattr(request.app.state, "audit_sink", None)


async def _record_audit(
    request: Request,
    *,
    action: str,
    resource: str,
    after: dict[str, object] | None = None,
    before: dict[str, object] | None = None,
) -> None:
    sink = _audit_sink(request)
    if sink is None:
        return
    await sink.record(
        AuditRecord(
            actor=AuditActor(actor_kind="api"),
            action=action,
            resource=resource,
            before=before,
            after=after,
            trace_id=str(getattr(request.state, "trace_id", "")) or None,
        )
    )


@router.post("", response_model=ObservationEvent)
async def create_event(payload: ObservationEventCreate, request: Request) -> ObservationEvent:
    event = await _event_repo(request).upsert(payload)
    await _record_audit(
        request,
        action="event.upsert",
        resource=f"observation_event:{event.event_id}",
        after=event.model_dump(mode="json"),
    )
    return event


@router.get("", response_model=list[ObservationEvent])
async def list_events(
    request: Request,
    baby_id: str = Query(min_length=1),
    include_deleted: bool = False,
) -> list[ObservationEvent]:
    return await _event_repo(request).list_by_baby(baby_id, include_deleted=include_deleted)


@router.get("/{event_id}", response_model=ObservationEvent)
async def get_event(event_id: str, request: Request) -> ObservationEvent:
    event = await _event_repo(request).get(event_id)
    if event is None:
        raise NotFoundError("Event not found", evidence={"event_id": event_id})
    return event


@router.post("/{event_id}/correct", response_model=ObservationEvent)
async def correct_event(
    event_id: str,
    payload: EventCorrectionRequest,
    request: Request,
) -> ObservationEvent:
    event = await _event_repo(request).correct(event_id, payload)
    await _record_audit(
        request,
        action="event.correct",
        resource=f"observation_event:{event_id}",
        after=event.model_dump(mode="json"),
    )
    return event


@router.delete("/{event_id}", response_model=ObservationEvent)
async def delete_event(event_id: str, request: Request) -> ObservationEvent:
    event = await _event_repo(request).soft_delete(event_id)
    await _record_audit(
        request,
        action="event.soft_delete",
        resource=f"observation_event:{event_id}",
        after=event.model_dump(mode="json"),
    )
    return event
