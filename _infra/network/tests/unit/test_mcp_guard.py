# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:02:00

"""Unit tests for MCPGuard core abstraction (E2-C4-S1-T1)."""

import json

import pytest

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.models import GuardDecision, MCPToolCall, MCPToolResult, PolicyDecision
from _infra.network.mcp_guard.schema_validator import MCPToolSchemaValidator

SCHEMA_A = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
SCHEMA_B = {
    "type": "object",
    "properties": {"query": {"type": "string"}, "leak": {"type": "string"}},
    "required": ["query"],
}


def build_guard(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    schema_validator = MCPToolSchemaValidator(
        lockfile_path=tmp_path / "mcp_lockfile.yaml",
        audit_db_path=tmp_path / "audit.db",
    )
    return MCPGuard(audit_logger=audit, schema_validator=schema_validator, enable_mode_policy=False), audit


def test_mcp_models_instantiation():
    call = MCPToolCall(
        server_id="search-server",
        tool_name="search",
        args={"query": "hello"},
        mode="research",
        schema=SCHEMA_A,
        trace_id="trace-1",
    )
    result = MCPToolResult(success=True, result={"ok": True})
    decision = GuardDecision(
        decision=PolicyDecision.ALLOW,
        reason="unit",
        server_id=call.server_id,
        tool_name=call.tool_name,
        mode=call.mode,
    )

    assert call.args["query"] == "hello"
    assert result.success is True
    assert decision.allowed is True
    assert decision.denied is False
    assert decision.requires_approval is False


def test_mcp_tool_call_rejects_invalid_mode():
    with pytest.raises(ValueError):
        MCPToolCall(server_id="s", tool_name="t", mode="invalid")  # type: ignore[arg-type]


def test_guard_check_allows_and_writes_audit(tmp_path):
    guard, audit = build_guard(tmp_path)
    call = MCPToolCall(
        server_id="search-server",
        tool_name="search",
        args={"query": "hello", "limit": 3},
        mode="research",
        trace_id="trace-1",
    )

    decision = guard.check(call)

    assert decision.decision == PolicyDecision.ALLOW
    assert decision.allowed is True
    assert decision.audit_event_id is not None

    rows = audit.query(event_type="tool_call", limit=10)
    assert len(rows) == 1
    assert rows[0]["server_id"] == "search-server"
    assert rows[0]["tool_name"] == "search"
    assert rows[0]["decision"] == "allow"
    details = json.loads(rows[0]["details"])
    assert details["arg_keys"] == ["limit", "query"]
    assert details["trace_id"] == "trace-1"
    assert "hello" not in rows[0]["details"]  # do not log raw arg values


def test_guard_check_pins_schema_then_allows(tmp_path):
    guard, audit = build_guard(tmp_path)
    call = MCPToolCall(server_id="search-server", tool_name="search", schema=SCHEMA_A)

    first = guard.check(call)
    second = guard.check(call)

    assert first.allowed is True
    assert first.details["schema_status"] == "pinned"
    assert second.allowed is True
    assert second.details["schema_status"] == "unchanged"
    assert len(audit.query(event_type="tool_call", limit=10)) == 2


def test_guard_denies_schema_change_and_writes_audit(tmp_path):
    guard, audit = build_guard(tmp_path)
    guard.check(MCPToolCall(server_id="search-server", tool_name="search", schema=SCHEMA_A))

    decision = guard.check(MCPToolCall(server_id="search-server", tool_name="search", schema=SCHEMA_B))

    assert decision.denied is True
    assert decision.reason == "schema_changed"
    assert decision.details["old_hash"] != decision.details["new_hash"]

    rows = audit.query(event_type="tool_call", limit=10)
    assert rows[0]["decision"] == "deny"
    details = json.loads(rows[0]["details"])
    assert details["reason"] == "schema_changed"


def test_guard_verify_and_record_schema_methods(tmp_path):
    guard, _audit = build_guard(tmp_path)

    guard.record_schema("server", "tool", SCHEMA_A)

    assert guard.verify_schema("server", "tool", SCHEMA_A) is True


def test_guard_default_require_approval_decision_is_audited(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    validator = MCPToolSchemaValidator(tmp_path / "mcp_lockfile.yaml", tmp_path / "audit.db")
    guard = MCPGuard(audit_logger=audit, schema_validator=validator, default_decision=PolicyDecision.REQUIRE_APPROVAL, enable_mode_policy=False)

    decision = guard.check(MCPToolCall(server_id="browser", tool_name="click", mode="private"))

    assert decision.requires_approval is True
    rows = audit.query(event_type="tool_call", limit=10)
    assert rows[0]["decision"] == "require_approval"
