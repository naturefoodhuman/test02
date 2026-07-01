# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import (
    ContextPackage,
    ContextSection,
    EscalationPackage,
    ExternalResponse,
    ExternalSession,
    GatewayCapabilities,
    HumanAction,
)


def test_context_package_yaml_round_trip():
    ctx = ContextPackage(
        id="ctx_001",
        case_id="case_001",
        sections=[ContextSection(id="role", title="Role", content="You are reviewer", token_estimate=4)],
    )
    loaded = ContextPackage.from_yaml_text(ctx.to_yaml_text())
    assert loaded.sections[0].title == "Role"


def test_package_json_round_trip():
    pkg = EscalationPackage(id="pkg_001", case_id="case_001", context_package_id="ctx_001", content_hash="sha256:abc")
    loaded = EscalationPackage.model_validate_json(pkg.model_dump_json())
    assert loaded.gateway == "clipboard"
    assert loaded.content_hash == "sha256:abc"


def test_session_human_actions_serialization():
    session = ExternalSession(id="session_001", case_id="case_001", package_id="pkg_001", human_actions=[HumanAction(type="copied_to_clipboard")])
    assert session.human_actions[0].type == "copied_to_clipboard"
    assert "copied_to_clipboard" in session.to_json_text()


def test_response_hash_and_gateway_capabilities():
    response = ExternalResponse(id="resp_001", case_id="case_001", session_id="session_001", raw_ref="responses/raw.md", content_hash="sha256:abc")
    assert response.content_hash == "sha256:abc"
    caps = GatewayCapabilities(gateway="clipboard", supports_clipboard=True, enabled=True)
    assert caps.supports_clipboard is True
