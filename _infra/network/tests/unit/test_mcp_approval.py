# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:25:00

"""Unit tests for high-risk MCP approval flow (E2-C4-S1-T3)."""

import json

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.mcp_guard.approval import HighRiskApprovalEngine
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.models import MCPToolCall
from _infra.network.mcp_guard.schema_validator import MCPToolSchemaValidator


def test_high_risk_tool_name_is_detected():
    engine = HighRiskApprovalEngine(input_func=lambda _prompt: "yes")
    check = engine.check_requires_approval(MCPToolCall(server_id="social", tool_name="post", mode="research"))

    assert check.requires_approval is True
    assert check.reason == "high_risk_action:post"
    assert "post" in check.matched_terms


def test_high_risk_argument_is_detected():
    engine = HighRiskApprovalEngine(input_func=lambda _prompt: "yes")
    call = MCPToolCall(server_id="browser", tool_name="action", args={"action_type": "submit_form"}, mode="research")

    check = engine.check_requires_approval(call)

    assert check.requires_approval is True
    assert "submit_form" in check.matched_terms


def test_approval_requires_strict_lowercase_yes():
    engine_yes = HighRiskApprovalEngine(input_func=lambda _prompt: "yes")
    engine_no = HighRiskApprovalEngine(input_func=lambda _prompt: "YES")
    call = MCPToolCall(server_id="social", tool_name="post", mode="research")

    assert engine_yes.request_approval(call).approved is True
    assert engine_no.request_approval(call).approved is False


def build_guard(tmp_path, response: str):
    audit = AuditLogger(tmp_path / "audit.db")
    validator = MCPToolSchemaValidator(tmp_path / "mcp_lockfile.yaml", tmp_path / "audit.db")
    approval = HighRiskApprovalEngine(input_func=lambda _prompt: response)
    guard = MCPGuard(
        audit_logger=audit,
        schema_validator=validator,
        approval_engine=approval,
        enable_mode_policy=False,
        enable_argument_validation=False,
    )
    return guard, audit


def test_guard_approved_high_risk_call_allows_once_and_audits(tmp_path):
    guard, audit = build_guard(tmp_path, "yes")
    call = MCPToolCall(server_id="social", tool_name="post", args={"payload": "hello world"}, mode="research")

    decision = guard.check(call)

    assert decision.allowed is True
    assert decision.reason == "human_approved"
    rows = audit.query(event_type="tool_call", limit=5)
    assert rows[0]["decision"] == "allow"
    details = json.loads(rows[0]["details"])
    assert details["high_risk"] is True
    assert details["approved"] is True
    assert "payload" in details["arg_keys"]
    assert "hello world" not in rows[0]["details"]


def test_guard_rejected_high_risk_call_denies_and_audits(tmp_path):
    guard, audit = build_guard(tmp_path, "no")
    call = MCPToolCall(server_id="mail", tool_name="send_email", args={"to": "a@example.com"}, mode="research")

    decision = guard.check(call)

    assert decision.denied is True
    assert decision.reason == "human_rejected"
    rows = audit.query(event_type="tool_call", limit=5)
    assert rows[0]["decision"] == "deny"
    details = json.loads(rows[0]["details"])
    assert details["approved"] is False
    assert details["approval_reason"] == "high_risk_action:send_email"


def test_non_high_risk_call_does_not_prompt():
    prompted = {"count": 0}

    def input_func(_prompt):
        prompted["count"] += 1
        return "no"

    engine = HighRiskApprovalEngine(input_func=input_func)
    check = engine.check_requires_approval(MCPToolCall(server_id="search", tool_name="query", mode="research"))

    assert check.requires_approval is False
    assert prompted["count"] == 0
