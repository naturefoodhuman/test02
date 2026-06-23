# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:45:00

"""Security tests for cookie / storage leak blocking (E11-C5-S1-T1)."""

import asyncio

import pytest

from _infra.network.mcp_guard.argument_validator import ArgumentValidator
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.models import MCPToolCall
from _infra.network.privacy_gateway.canary import CanaryTokenMonitor
from _infra.network.privacy_gateway.gateway import PrivacyGateway


def run(coro):
    return asyncio.run(coro)


def build_guard() -> MCPGuard:
    return MCPGuard(
        enable_mode_policy=False,
        enable_approval=False,
        argument_validator=ArgumentValidator(detect_pii=False, detect_secret=False),
    )


@pytest.mark.parametrize(
    "script",
    [
        "return document.cookie",
        "return window.localStorage.getItem('token')",
        "return window.sessionStorage.getItem('sid')",
        "return eval('document.cookie')",
        "return Function('return document.cookie')()",
    ],
)
def test_mcp_guard_blocks_cookie_and_storage_js_arguments(script):
    guard = build_guard()
    call = MCPToolCall(
        server_id="chrome-devtools-private",
        tool_name="evaluate_js",
        args={"script": script},
        mode="private",
    )

    decision = guard.check(call)

    assert decision.denied is True
    assert decision.reason == "forbidden_argument_pattern"
    assert decision.details["reason"] == "argument_validation_denied"


def test_argument_validator_blocks_cookie_header_secret():
    validator = ArgumentValidator(detect_pii=False, detect_secret=True)
    call = MCPToolCall(
        server_id="browser",
        tool_name="submit_form",
        args={"headers": {"Cookie": "sessionid=abcdef1234567890; csrftoken=secret123"}},
        mode="private",
    )

    result = validator.validate(call)

    assert result.allowed is False
    assert result.reason == "secret_detected_in_arguments"
    assert "COOKIE" in result.matches or "SESSION_ID" in result.matches


def test_privacy_gateway_redacts_cookie_header_in_output_layer():
    gateway = PrivacyGateway(
        detectors=[],
        ner_detector=None,
        qwen_classifier=None,
        canary_monitor=CanaryTokenMonitor(tokens=["COOKIE_CANARY"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    result = run(gateway.process_text("Response headers: Cookie: sessionid=abcdef1234567890; theme=dark"))

    detected_types = {entity["type"] for entity in result.detections}
    assert "COOKIE" in detected_types or "SESSION_ID" in detected_types
    assert "sessionid=abcdef" not in result.text
    assert "PII_COOKIE" in result.text or "PII_SESSION_ID" in result.text


def test_privacy_gateway_redacts_set_cookie_header_in_output_layer():
    gateway = PrivacyGateway(
        detectors=[],
        ner_detector=None,
        qwen_classifier=None,
        canary_monitor=CanaryTokenMonitor(tokens=["COOKIE_CANARY"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    result = run(gateway.process_text("Set-Cookie: connect.sid=s%3Aabcdef1234567890; HttpOnly"))

    assert "connect.sid" not in result.text
    assert any(entity["type"] == "COOKIE" for entity in result.detections)


def test_clean_non_cookie_arguments_are_allowed():
    guard = build_guard()
    call = MCPToolCall(
        server_id="chrome-devtools-private",
        tool_name="snapshot",
        args={"selector": "main"},
        mode="private",
    )

    decision = guard.check(call)

    assert decision.allowed is True
