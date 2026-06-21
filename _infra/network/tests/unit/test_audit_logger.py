# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:32:00 CST

"""单元测试：AuditLogger（内存 + 真实 DB）"""

import tempfile
import os
from pathlib import Path

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.audit_log.models import AuditEvent


def test_record_and_query(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(db_path)

    eid = logger.record_tool_call(
        server_id="searxng",
        tool_name="search",
        mode="research",
        decision="allow",
        details={"query": "test"}
    )
    assert eid

    results = logger.query(limit=5)
    assert len(results) >= 1
    assert results[0]["tool_name"] == "search"
    assert results[0]["decision"] == "allow"

    logger.close()


def test_record_canary(tmp_path):
    db_path = tmp_path / "audit.db"
    logger = AuditLogger(db_path)

    event = AuditEvent(
        event_type="canary_hit",
        server_id="crawl4ai",
        tool_name="extract",
        mode="research",
        decision="block",
        details={"token": "AI_CANARY_2026_TEST", "location": "markdown"}
    )
    logger.record(event)

    hits = logger.query(event_type="canary_hit", limit=3)
    assert len(hits) == 1
    assert "AI_CANARY" in hits[0]["details"]

    logger.close()
