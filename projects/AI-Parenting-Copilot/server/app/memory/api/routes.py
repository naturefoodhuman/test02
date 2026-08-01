# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 22:22:00

"""Family memory API routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import AppError
from server.app.memory.family_knowledge_repo import (
    FamilyKnowledgeRecord,
    InMemoryFamilyKnowledgeRepository,
    SQLAlchemyFamilyKnowledgeRepository,
    UpsertFamilyKnowledgeRequest,
)
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1/family-knowledge", tags=["memory"])


def _repo(
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


@router.post("", response_model=FamilyKnowledgeRecord)
async def upsert_family_knowledge(
    payload: UpsertFamilyKnowledgeRequest,
    request: Request,
) -> FamilyKnowledgeRecord:
    record = await _repo(request).upsert(payload)
    await record_request_audit(
        request,
        action="family_knowledge.upsert",
        resource=f"family_knowledge:{record.family_id}:{record.key}",
        after=record.model_dump(mode="json"),
    )
    return record


@router.get("/{family_id}", response_model=list[FamilyKnowledgeRecord])
async def list_family_knowledge(family_id: str, request: Request) -> list[FamilyKnowledgeRecord]:
    return await _repo(request).list_by_family(family_id)
