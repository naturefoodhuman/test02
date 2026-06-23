# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:25:00

"""Unit tests for MCP argument validator (E2-C4-S1-T4)."""

import json

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.mcp_guard.argument_validator import ArgumentValidator
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.models import MCPToolCall
from _infra.network.mcp_guard.schema_validator import MCPToolSchemaValidator


def test_document_cookie_is_blocked():
    validator = ArgumentValidator(detect_pii=False, detect_secret=False)
    result = validator.validate(MCPToolCall(server_id="browser", tool_name="evaluate_js", args={"script": "document.cookie"}))

    assert result.allowed is False
    assert result.reason == "forbidden_argument_pattern"


def test_url_allowlist_blocks_disallowed_domain():
    validator = ArgumentValidator(allowed_url_domains=["example.com"], detect_pii=False, detect_secret=False)
    result = validator.validate(MCPToolCall(server_id="fetch", tool_name="get", args={"url": "https://evil.test/page"}))

    assert result.allowed is False
    assert result.reason == "url_not_allowed"
    assert result.matches == ("https://evil.test/page",)


def test_url_allowlist_allows_subdomain():
    validator = ArgumentValidator(allowed_url_domains=["example.com"], detect_pii=False, detect_secret=False)
    result = validator.validate(MCPToolCall(server_id="fetch", tool_name="get", args={"url": "https://docs.example.com/page"}))

    assert result.allowed is True


def test_max_argument_length_blocks():
    validator = ArgumentValidator(max_arg_length=20, detect_pii=False, detect_secret=False)
    result = validator.validate(MCPToolCall(server_id="x", tool_name="y", args={"text": "x" * 100}))

    assert result.allowed is False
    assert result.reason == "arguments_too_long"


def test_secret_in_arguments_is_blocked():
    validator = ArgumentValidator(detect_pii=False, detect_secret=True)
    result = validator.validate(
        MCPToolCall(server_id="api", tool_name="call", args={"api_key": "sk-proj-abcdefghijklmnopqrstuvwxyz123456"})
    )

    assert result.allowed is False
    assert result.reason == "secret_detected_in_arguments"


def test_pii_in_arguments_is_blocked():
    validator = ArgumentValidator(detect_pii=True, detect_secret=False)
    result = validator.validate(MCPToolCall(server_id="search", tool_name="query", args={"q": "phone 13855551234"}))

    assert result.allowed is False
    assert result.reason == "pii_detected_in_arguments"


def test_mcp_guard_denies_bad_arguments_and_audits_without_raw_values(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    schema_validator = MCPToolSchemaValidator(tmp_path / "mcp_lockfile.yaml", tmp_path / "audit.db")
    guard = MCPGuard(
        audit_logger=audit,
        schema_validator=schema_validator,
        argument_validator=ArgumentValidator(detect_pii=False, detect_secret=False),
        enable_mode_policy=False,
        enable_approval=False,
    )

    decision = guard.check(MCPToolCall(server_id="browser", tool_name="evaluate_js", args={"script": "document.cookie"}))

    assert decision.denied is True
    assert decision.reason == "forbidden_argument_pattern"
    rows = audit.query(event_type="tool_call", limit=5)
    assert rows[0]["decision"] == "deny"
    details = json.loads(rows[0]["details"])
    assert details["reason"] == "argument_validation_denied"
    assert details["argument_validation_reason"] == "forbidden_argument_pattern"
    assert "document.cookie" not in rows[0]["details"]
