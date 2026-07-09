# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 00:30:00


"""Append-only audit logging service."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from server.app.common.clock import utc_now
from server.app.common.errors import AppError
from server.app.common.ids import new_ulid
from server.app.models import AuditLog

JsonDict = dict[str, Any]


class AuditWriteError(AppError):
    """Raised when a required audit write fails."""

    status_code = 500
    code = "AUDIT_WRITE_FAILED"


@dataclass(frozen=True)
class AuditActor:
    """Actor metadata stored as JSONB in audit_log.actor."""

    actor_kind: str
    actor_id: str | None = None
    family_id: str | None = None
    user_id: str | None = None
    device_id: str | None = None

    def to_dict(self) -> JsonDict:
        return {
            "actor_kind": self.actor_kind,
            "actor_id": self.actor_id,
            "family_id": self.family_id,
            "user_id": self.user_id,
            "device_id": self.device_id,
        }


@dataclass(frozen=True)
class AuditRecord:
    """Canonical audit record before persistence."""

    action: str
    resource: str
    actor: AuditActor = field(default_factory=lambda: AuditActor(actor_kind="system"))
    before: JsonDict | None = None
    after: JsonDict | None = None
    rule_version: str | None = None
    llm_call_id: str | None = None
    trace_id: str | None = None
    audit_id: str = field(default_factory=new_ulid)


class AuditSink(Protocol):
    """Minimal protocol consumed by the `@audit` decorator."""

    async def record(self, record: AuditRecord) -> None:
        """Persist or collect an audit record."""


class AuditService:
    """SQLAlchemy-backed audit writer.

    Database immutability is enforced by `0001_initial_schema` via triggers and
    grants. This service intentionally exposes no update/delete operations.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def record(self, record: AuditRecord) -> None:
        """Insert an append-only audit record."""

        try:
            async with self.session_factory() as session:
                async with session.begin():
                    session.add(
                        AuditLog(
                            id=record.audit_id,
                            ts=utc_now(),
                            actor=record.actor.to_dict(),
                            action=record.action,
                            resource=record.resource,
                            before_state=record.before,
                            after_state=record.after,
                            rule_version=record.rule_version,
                            llm_call_id=record.llm_call_id,
                            trace_id=record.trace_id,
                        )
                    )
        except Exception as exc:
            raise AuditWriteError(
                "Audit record could not be written",
                evidence={"action": record.action, "resource": record.resource},
            ) from exc

    async def list_recent(self, session: AsyncSession, *, limit: int = 100) -> Sequence[AuditLog]:
        """Read-only helper for tests/admin views."""

        result = await session.execute(select(AuditLog).order_by(AuditLog.ts.desc()).limit(limit))
        return result.scalars().all()


class MemoryAuditSink:
    """Deterministic audit sink for unit tests and fakes."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    async def record(self, record: AuditRecord) -> None:
        self.records.append(record)
