# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:02:00

"""Unit tests for MCP mode permission policy (E2-C4-S1-T2)."""

import json

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.mode_policy import ModePolicyEngine
from _infra.network.mcp_guard.models import MCPToolCall
from _infra.network.mcp_guard.schema_validator import MCPToolSchemaValidator


def test_mode_policy_coding_rejects_browser():
    engine = ModePolicyEngine.from_config()
    call = MCPToolCall(server_id="playwright", tool_name="snapshot", mode="coding")

    result = engine.evaluate(call)

    assert result.allowed is False
    assert result.reason == "server_denied:playwright"


def test_mode_policy_research_rejects_shell():
    engine = ModePolicyEngine.from_config()
    call = MCPToolCall(server_id="shell", tool_name="execute_shell", mode="research")

    result = engine.evaluate(call)

    assert result.allowed is False
    assert result.reason == "server_denied:shell"


def test_mode_policy_private_is_read_only():
    engine = ModePolicyEngine.from_config()
    read_call = MCPToolCall(server_id="chrome-devtools-private", tool_name="snapshot", mode="private")
    write_call = MCPToolCall(server_id="chrome-devtools-private", tool_name="click", mode="private")

    assert engine.check_mode_policy(read_call) is True
    denied = engine.evaluate(write_call)
    assert denied.allowed is False
    assert denied.reason == "tool_forbidden:click"


def test_mode_policy_config_changes_are_loaded(tmp_path):
    policy_file = tmp_path / "mode_policies.yaml"
    policy_file.write_text(
        "version: '1.0'\n"
        "modes:\n"
        "  research:\n"
        "    allowed_servers: ['custom-search']\n"
        "    denied_servers: []\n"
        "    allowed_tools: ['safe_*']\n"
        "    forbidden_tools: []\n",
        encoding="utf-8",
    )
    engine = ModePolicyEngine.from_config(policy_file)

    assert engine.check_mode_policy(MCPToolCall(server_id="custom-search", tool_name="safe_query", mode="research")) is True
    assert engine.check_mode_policy(MCPToolCall(server_id="custom-search", tool_name="unsafe_query", mode="research")) is False
    assert engine.check_mode_policy(MCPToolCall(server_id="searxng", tool_name="safe_query", mode="research")) is False


def test_mcp_guard_denies_mode_policy_and_audits(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    validator = MCPToolSchemaValidator(tmp_path / "mcp_lockfile.yaml", tmp_path / "audit.db")
    guard = MCPGuard(audit_logger=audit, schema_validator=validator, mode_policy=ModePolicyEngine.from_config())

    decision = guard.check(MCPToolCall(server_id="shell", tool_name="execute_shell", args={"cmd": "echo secret"}, mode="research"))

    assert decision.denied is True
    assert decision.reason == "server_denied:shell"
    rows = audit.query(event_type="tool_call", limit=5)
    assert rows[0]["decision"] == "deny"
    details = json.loads(rows[0]["details"])
    assert details["reason"] == "mode_policy_denied"
    assert details["mode_policy_reason"] == "server_denied:shell"
    assert "echo secret" not in rows[0]["details"]


def test_mcp_guard_allows_mode_policy_then_schema_check(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    validator = MCPToolSchemaValidator(tmp_path / "mcp_lockfile.yaml", tmp_path / "audit.db")
    guard = MCPGuard(audit_logger=audit, schema_validator=validator, mode_policy=ModePolicyEngine.from_config())

    decision = guard.check(
        MCPToolCall(
            server_id="searxng",
            tool_name="search",
            mode="research",
            schema={"type": "object", "properties": {"q": {"type": "string"}}},
        )
    )

    assert decision.allowed is True
    assert decision.details["mode_policy_reason"] == "mode_policy_allow"
    assert decision.details["schema_status"] == "pinned"
