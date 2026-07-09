# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


"""APC-T058 static audit immutability regression tests."""
from __future__ import annotations

from pathlib import Path


def test_audit_log_immutability_trigger_exists() -> None:
    migration = Path("server/migrations/versions/0001_initial_schema.py").read_text()

    assert "prevent_audit_log_mutation" in migration
    assert "trg_audit_log_no_update" in migration
    assert "trg_audit_log_no_delete" in migration
    assert "REVOKE UPDATE, DELETE ON TABLE audit_log" in migration
