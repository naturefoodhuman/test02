# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:35:00

"""Unit tests for PlaywrightOrchestrator (E7-C2-S1-T2)."""

import asyncio

import pytest

from _infra.network.browser.playwright_client import PlaywrightMCPClient
from _infra.network.browser.playwright_orchestrator import PlaywrightOrchestrator
from _infra.network.browser.profile_manager import ProfileManager
from _infra.network.config_loader.schemas import NetworkConfig
from _infra.network.exceptions import SessionExpiredError
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.mode_policy import ModePolicyEngine
from _infra.network.mcp_guard.models import PolicyDecision


class FakePlaywrightTransport:
    def __init__(self, snapshot_text="Public page text"):
        self.snapshot_text = snapshot_text
        self.calls = []

    async def navigate(self, url, timeout_ms):
        self.calls.append(("navigate", url, timeout_ms))
        return {"ok": True}

    async def snapshot(self, timeout_ms):
        self.calls.append(("snapshot", timeout_ms))
        return {"text": self.snapshot_text}

    async def click(self, ref, timeout_ms):
        self.calls.append(("click", ref, timeout_ms))
        return {"clicked": ref}

    async def type_text(self, ref, text, timeout_ms):
        self.calls.append(("type", ref, text, timeout_ms))
        return {"typed": True}

    async def wait(self, ms, timeout_ms):
        self.calls.append(("wait", ms, timeout_ms))
        return {"waited": ms}

    async def close(self, timeout_ms):
        self.calls.append(("close", timeout_ms))
        return {"closed": True}


def make_orchestrator(tmp_path, snapshot_text="Public page text"):
    cfg = NetworkConfig(
        browser={
            "profiles": {
                "ai_public": {
                    "user_data_dir": "${HOME}/ai-agent/profiles/ai-public",
                    "blocked_origins": ["https://accounts.google.com"],
                }
            }
        }
    )
    profile_manager = ProfileManager(config=cfg, profile_root=tmp_path)
    guard = MCPGuard(mode_policy=ModePolicyEngine.from_config(), default_decision=PolicyDecision.ALLOW)
    transport = FakePlaywrightTransport(snapshot_text=snapshot_text)
    client = PlaywrightMCPClient(guard=guard, transport=transport)
    return PlaywrightOrchestrator(client=client, profile_manager=profile_manager), transport


def test_go_and_extract_public_page(tmp_path):
    orchestrator, transport = make_orchestrator(tmp_path, "Welcome public page")

    result = asyncio.run(orchestrator.go_and_extract("https://example.com"))

    assert result.url == "https://example.com"
    assert result.text == "Welcome public page"
    assert result.profile.name == "ai_public"
    assert result.session.expired is False
    assert (tmp_path / "ai-public").exists()
    assert transport.calls == [("navigate", "https://example.com", 30000), ("snapshot", 10000)]


def test_go_and_extract_blocks_login_page(tmp_path):
    orchestrator, _transport = make_orchestrator(tmp_path, "Sign in required. CAPTCHA")

    with pytest.raises(SessionExpiredError):
        asyncio.run(orchestrator.go_and_extract("https://example.com/login"))


def test_fill_form_field_delegates_to_guarded_client(tmp_path):
    orchestrator, transport = make_orchestrator(tmp_path)

    result = asyncio.run(orchestrator.fill_form_field("input-1", "hello"))

    assert result == {"typed": True}
    assert transport.calls == [("type", "input-1", "hello", 10000)]


def test_close_delegates_to_client(tmp_path):
    orchestrator, transport = make_orchestrator(tmp_path)

    result = asyncio.run(orchestrator.close())

    assert result == {"closed": True}
    assert transport.calls == [("close", 10000)]
