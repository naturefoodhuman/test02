# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""审计服务集成测试（APC-T006，需 DB）。

连 AI_parenting_dev 库验证：
    - AuditService.append 插入 audit_log 成功，字段齐全（含 trace_id/request_id 嵌入 after）。
    - audit_log 对 parenting 角色 UPDATE/DELETE 被拒绝（§22.2 append-only）。
    - 审计写入失败 → UpstreamUnavailable（不得静默成功）。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
每个测试用单一 asyncio.run（避免跨事件循环的 engine 死连接问题）。
"""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import text

from server.app import db as db_module
from server.app.common.clock import SystemClock
from server.app.common.errors import UpstreamUnavailable
from server.app.db import get_session_factory
from server.app.models.rules import AuditLog
from server.app.observability.audit import AuditService
from server.app.observability.logger import bind_context, clear_context

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset_db():
    """同步重置进程级 engine 缓存（避免跨测试死连接）。"""
    db_module.reset_db()
    clear_context()
    yield
    db_module.reset_db()
    clear_context()


def test_audit_service_inserts_record_with_all_fields():
    """AuditService.append 插入 audit_log，字段齐全（§6.1 + trace_id/request_id 嵌入 after）。"""

    async def run() -> dict:
        bind_context(trace_id="01JTRACETEST00000000000000", request_id="01JREQTEST00000000000000")
        factory = get_session_factory()
        async with factory() as session:
            svc = AuditService(session, SystemClock())
            audit_id = await svc.append(
                actor="01JUSER",
                action="create",
                resource="observation_event/01JEVT",
                before=None,
                after={"event_id": "01JEVT", "amount_ml": 120},
            )
            await session.commit()
            # 同 session 读回验证（避免跨连接/循环问题）。
            from sqlalchemy import select

            row = (
                await session.execute(
                    select(
                        AuditLog.id,
                        AuditLog.actor,
                        AuditLog.action,
                        AuditLog.resource,
                        AuditLog.before,
                        AuditLog.after,
                        AuditLog.rule_version,
                        AuditLog.llm_call_id,
                    ).where(AuditLog.id == audit_id)
                )
            ).one()
        return dict(row._mapping)

    row = asyncio.run(run())
    assert row["actor"] == "01JUSER"
    assert row["action"] == "create"
    assert row["resource"] == "observation_event/01JEVT"
    assert row["before"] is None
    assert row["after"]["event_id"] == "01JEVT"
    assert row["after"]["amount_ml"] == 120
    # trace_id/request_id 嵌入 after JSONB
    assert row["after"]["_trace_id"] == "01JTRACETEST00000000000000"
    assert row["after"]["_request_id"] == "01JREQTEST00000000000000"
    assert row["rule_version"] is None
    assert row["llm_call_id"] is None


def test_audit_log_update_rejected_for_parenting_role():
    """audit_log 对 parenting 角色 UPDATE 被拒绝（§22.2 append-only，REVOKE）。"""

    async def run() -> bool:
        factory = get_session_factory()
        async with factory() as session:
            svc = AuditService(session, SystemClock())
            audit_id = await svc.append(actor="01JUSER", action="create", resource="test")
            await session.commit()
            # 尝试 UPDATE（迁移层已 REVOKE，应抛权限错误）。
            try:
                await session.execute(
                    text("UPDATE audit_log SET actor='tampered' WHERE id = :id"),
                    {"id": audit_id},
                )
                await session.commit()
                return True  # 居然成功 = 严重违规
            except Exception:
                return False  # 被拒绝（符合预期）

    updated = asyncio.run(run())
    assert not updated, "audit_log 不应允许 UPDATE（append-only 被破坏）"


def test_audit_log_delete_rejected_for_parenting_role():
    """audit_log 对 parenting 角色 DELETE 被拒绝（§22.2 append-only，REVOKE）。"""

    async def run() -> bool:
        factory = get_session_factory()
        async with factory() as session:
            svc = AuditService(session, SystemClock())
            audit_id = await svc.append(actor="01JUSER", action="create", resource="test")
            await session.commit()
            try:
                await session.execute(
                    text("DELETE FROM audit_log WHERE id = :id"), {"id": audit_id}
                )
                await session.commit()
                return True
            except Exception:
                return False

    deleted = asyncio.run(run())
    assert not deleted, "audit_log 不应允许 DELETE（append-only 被破坏）"


def test_audit_write_failure_raises_upstream_unavailable():
    """审计写入失败（如违反约束）→ UpstreamUnavailable，不得静默成功（§10.4）。"""

    async def run():
        factory = get_session_factory()
        async with factory() as session:
            svc = AuditService(session, SystemClock())
            # action 超长（String(64)）触发 DB 约束错误 → AuditService 映射为 UpstreamUnavailable。
            with pytest.raises(UpstreamUnavailable):
                await svc.append(actor="01JUSER", action="x" * 200, resource="test")

    asyncio.run(run())
