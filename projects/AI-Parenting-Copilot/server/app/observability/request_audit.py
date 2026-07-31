# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 21:25:00

"""Request-scoped audit helper for API routes.

If a SQLAlchemy session is attached to request.state, audit records are inserted into
`audit_log` in the same request transaction. Otherwise the helper falls back to the
in-memory AuditSink used by dev tests.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.models import AuditLog
from server.app.observability.audit import AuditActor, AuditRecord, AuditSink


async def record_request_audit(
    request: Request,
    *,
    action: str,
    resource: str,
    actor_kind: str = "api",
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    db_only: bool = False,
) -> None:
    """Write audit record to DB session or dev sink."""

    trace_id = str(getattr(request.state, "trace_id", "")) or None
    db_session = getattr(request.state, "db_session", None)
    if isinstance(db_session, AsyncSession):
        db_session.add(
            AuditLog(
                ts=utc_now(),
                actor={"actor_kind": actor_kind},
                action=action,
                resource=resource,
                before_state=before,
                after_state=after,
                trace_id=trace_id,
            )
        )
        await db_session.flush()
        return
    if db_only:
        return
    sink = getattr(request.app.state, "audit_sink", None)
    if sink is None:
        return
    audit_sink: AuditSink = sink
    await audit_sink.record(
        AuditRecord(
            actor=AuditActor(actor_kind=actor_kind),
            action=action,
            resource=resource,
            before=before,
            after=after,
            trace_id=trace_id,
        )
    )
