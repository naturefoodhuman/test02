# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 00:30:00


"""APC-T006 audit decorator tests."""

from __future__ import annotations

import pytest

from server.app.common.audit_decorator import audit
from server.app.observability.audit import AuditWriteError, MemoryAuditSink


@audit(
    action="baby.update",
    resource="baby",
    before=lambda *args, **kwargs: {"name": "old"},
    after=lambda *args, **kwargs: kwargs["result"],
)
async def mutate_baby(*, audit_sink: MemoryAuditSink) -> dict[str, str]:
    return {"name": "new"}


@audit(action="dangerous.write", resource="danger")
async def dangerous_without_sink() -> dict[str, str]:
    return {"ok": "true"}


@pytest.mark.asyncio
async def test_audit_decorator_records_before_after() -> None:
    sink = MemoryAuditSink()

    result = await mutate_baby(audit_sink=sink)

    assert result == {"name": "new"}
    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.action == "baby.update"
    assert record.resource == "baby"
    assert record.before == {"name": "old"}
    assert record.after == {"name": "new"}


@pytest.mark.asyncio
async def test_high_risk_audit_without_sink_blocks_operation_result() -> None:
    with pytest.raises(AuditWriteError):
        await dangerous_without_sink()
