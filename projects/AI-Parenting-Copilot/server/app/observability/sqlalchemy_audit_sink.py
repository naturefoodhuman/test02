# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 00:05:00

"""Request-scoped SQLAlchemy AuditSink implementation."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.models import AuditLog
from server.app.observability.audit import AuditRecord


class SQLAlchemyAuditSink:
    """Persist AuditRecord objects into the current request transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, record: AuditRecord) -> None:
        self.session.add(
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
        await self.session.flush()
