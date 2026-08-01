# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 22:20:00

"""FamilyKnowledge repository for family memory updates."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid
from server.app.models import FamilyKnowledge as ORMFamilyKnowledge


class FamilyKnowledgeRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    family_id: str
    key: str
    value: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class UpsertFamilyKnowledgeRequest(BaseModel):
    family_id: str
    key: str
    value: dict[str, Any] = Field(default_factory=dict)


class InMemoryFamilyKnowledgeRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], FamilyKnowledgeRecord] = {}

    async def upsert(self, request: UpsertFamilyKnowledgeRequest) -> FamilyKnowledgeRecord:
        key = (request.family_id, request.key)
        existing = self.records.get(key)
        if existing is None:
            record = FamilyKnowledgeRecord(**request.model_dump())
        else:
            record = existing.model_copy(
                update={
                    "value": request.value,
                    "version": existing.version + 1,
                    "updated_at": utc_now().isoformat(),
                }
            )
        self.records[key] = record
        return record

    async def list_by_family(self, family_id: str) -> list[FamilyKnowledgeRecord]:
        return [record for record in self.records.values() if record.family_id == family_id]


class SQLAlchemyFamilyKnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, request: UpsertFamilyKnowledgeRequest) -> FamilyKnowledgeRecord:
        row = await self.session.scalar(
            select(ORMFamilyKnowledge).where(
                ORMFamilyKnowledge.family_id == request.family_id,
                ORMFamilyKnowledge.key == request.key,
                ORMFamilyKnowledge.is_deleted.is_(False),
            )
        )
        now = utc_now()
        if row is None:
            row = ORMFamilyKnowledge(
                id=new_ulid(),
                family_id=request.family_id,
                key=request.key,
                value=request.value,
                version=1,
                created_at=now,
                updated_at=now,
            )
            self.session.add(row)
        else:
            row.value = request.value
            row.version += 1
            row.updated_at = now
        await self.session.flush()
        return self._to_record(row)

    async def list_by_family(self, family_id: str) -> list[FamilyKnowledgeRecord]:
        rows = await self.session.scalars(
            select(ORMFamilyKnowledge).where(
                ORMFamilyKnowledge.family_id == family_id,
                ORMFamilyKnowledge.is_deleted.is_(False),
            )
        )
        return [self._to_record(row) for row in rows]

    @staticmethod
    def _to_record(row: ORMFamilyKnowledge) -> FamilyKnowledgeRecord:
        return FamilyKnowledgeRecord(
            id=row.id,
            family_id=row.family_id,
            key=row.key,
            value=row.value,
            version=row.version,
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
        )
