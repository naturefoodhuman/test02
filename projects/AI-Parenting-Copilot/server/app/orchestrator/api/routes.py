# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-02 01:10:00

"""Orchestrator API routes."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.common.errors import AppError
from server.app.events.domain.observation_event import (
    EventSource,
    ObservationEvent,
    ObservationEventCreate,
)
from server.app.events.infra.repository import InMemoryEventRepository
from server.app.events.infra.sqlalchemy_repository import SQLAlchemyEventRepository
from server.app.memory.family_knowledge_repo import (
    InMemoryFamilyKnowledgeRepository,
    SQLAlchemyFamilyKnowledgeRepository,
    UpsertFamilyKnowledgeRequest,
)
from server.app.memory.sqlalchemy_store import SQLAlchemyMemoryStore
from server.app.observability.request_audit import record_request_audit
from server.app.observability.sqlalchemy_audit_sink import SQLAlchemyAuditSink
from server.app.orchestrator.orchestrator import (
    Orchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
)

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


class ConfirmRecordCandidateRequest(BaseModel):
    baby_id: str
    family_id: str
    event_type: str
    normalized_payload: dict[str, object] = Field(default_factory=dict)
    confidence: float = 1.0
    user_id: str | None = None
    device_id: str | None = None
    raw_text: str | None = None
    source: EventSource = EventSource.MANUAL
    start_time: datetime = Field(default_factory=utc_now)


class ConfirmFamilyMemoryRequest(BaseModel):
    family_id: str
    key: str
    value: object


def _orchestrator(request: Request) -> Orchestrator:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return Orchestrator(
            memory_store=SQLAlchemyMemoryStore(db_session),
            audit_sink=SQLAlchemyAuditSink(db_session),
        )
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        raise AppError(
            "Orchestrator is not configured",
            code="ORCHESTRATOR_UNAVAILABLE",
            status_code=500,
        )
    return cast(Orchestrator, orchestrator)


def _event_repo(request: Request) -> InMemoryEventRepository | SQLAlchemyEventRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemyEventRepository(db_session)
    repo = getattr(request.app.state, "event_repository", None)
    if repo is None:
        raise AppError("Event repository is not configured", code="EVENT_REPO_UNAVAILABLE")
    return cast(InMemoryEventRepository, repo)


def _family_knowledge_repo(
    request: Request,
) -> InMemoryFamilyKnowledgeRepository | SQLAlchemyFamilyKnowledgeRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemyFamilyKnowledgeRepository(db_session)
    repo = getattr(request.app.state, "family_knowledge_repository", None)
    if repo is None:
        raise AppError(
            "Family knowledge repository is not configured",
            code="MEMORY_REPO_UNAVAILABLE",
        )
    return cast(InMemoryFamilyKnowledgeRepository, repo)


@router.post("/query", response_model=OrchestratorResponse)
async def query(payload: OrchestratorRequest, request: Request) -> OrchestratorResponse:
    return await _orchestrator(request).handle(payload)


@router.post("/record-candidates/confirm", response_model=ObservationEvent)
async def confirm_record_candidate(
    payload: ConfirmRecordCandidateRequest,
    request: Request,
) -> ObservationEvent:
    event = await _event_repo(request).upsert(
        ObservationEventCreate(
            baby_id=payload.baby_id,
            family_id=payload.family_id,
            user_id=payload.user_id,
            device_id=payload.device_id,
            event_type=payload.event_type,
            start_time=payload.start_time,
            client_created_at=payload.start_time,
            raw_input={"text": payload.raw_text} if payload.raw_text else {},
            normalized_payload=payload.normalized_payload,
            payload=payload.normalized_payload,
            confidence=payload.confidence,
            source=payload.source,
        )
    )
    await record_request_audit(
        request,
        action="copilot.record_confirm",
        resource=f"observation_event:{event.event_id}",
        after=event.model_dump(mode="json"),
    )
    return event


@router.post("/family-memory/confirm", response_model=dict[str, object])
async def confirm_family_memory(
    payload: ConfirmFamilyMemoryRequest,
    request: Request,
) -> dict[str, object]:
    value = payload.value if isinstance(payload.value, dict) else {"value": payload.value}
    record = await _family_knowledge_repo(request).upsert(
        UpsertFamilyKnowledgeRequest(
            family_id=payload.family_id,
            key=payload.key,
            value=value,
        )
    )
    await record_request_audit(
        request,
        action="copilot.family_memory_confirm",
        resource=f"family_knowledge:{record.family_id}:{record.key}",
        after=record.model_dump(mode="json"),
    )
    return {"family_knowledge": record.model_dump(mode="json")}
