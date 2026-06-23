# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:16:58

"""Unit tests for PlaywrightMCPClient and pinned MCP metadata (E7-C1/E7-C2)."""

import asyncio
import json
from pathlib import Path

import pytest
import yaml

from _infra.network.browser.playwright_client import PlaywrightClientConfig, PlaywrightMCPClient
from _infra.network.exceptions import ForbiddenBrowserActionError
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.mode_policy import ModePolicyEngine
from _infra.network.mcp_guard.models import PolicyDecision

ROOT = Path(__file__).resolve().parents[4]


class FakePlaywrightTransport:
    def __init__(self):
        self.calls = []

    async def navigate(self, url, timeout_ms):
        self.calls.append(("navigate", url, timeout_ms))
        return {"ok": True, "url": url}

    async def snapshot(self, timeout_ms):
        self.calls.append(("snapshot", timeout_ms))
        return {"text": "Example page"}

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


def guard():
    return MCPGuard(
        mode_policy=ModePolicyEngine.from_config(),
        default_decision=PolicyDecision.ALLOW,
    )


def test_playwright_lockfile_entry_is_pinned():
    data = yaml.safe_load((ROOT / "config" / "mcp_lockfile.yaml").read_text(encoding="utf-8"))
    entry = data["servers"]["playwright-public"]

    assert entry["repo_url"] == "https://github.com/microsoft/playwright-mcp.git"
    assert entry["commit_hash"] == "0f4e6ff6be93c63af843c3d67894d83b37ae27a3"
    assert entry["package_name"] == "@playwright/mcp"
    assert entry["package_version"] == "0.0.76"
    assert entry["local_path"] == "mcp-servers/playwright-public"
    assert "--browser=chromium" in entry["mcp_args"]


def test_research_profile_points_to_playwright_pinned_local_path():
    profile = json.loads((ROOT / ".mcp.json.research").read_text(encoding="utf-8"))
    args = profile["mcpServers"]["playwright-public"]["args"]

    assert args[0] == "mcp-servers/playwright-public/cli.js"
    assert "--browser=chromium" in args
    assert "--timeout-navigation=30000" in args
    assert "--timeout-action=10000" in args


def test_playwright_client_navigation_and_snapshot():
    transport = FakePlaywrightTransport()
    client = PlaywrightMCPClient(guard=guard(), transport=transport)

    nav = asyncio.run(client.navigate("https://example.com"))
    snap = asyncio.run(client.snapshot())

    assert nav == {"ok": True, "url": "https://example.com"}
    assert snap == {"text": "Example page"}
    assert transport.calls == [("navigate", "https://example.com", 30000), ("snapshot", 10000)]


def test_playwright_client_actions_use_action_timeout():
    transport = FakePlaywrightTransport()
    client = PlaywrightMCPClient(guard=guard(), transport=transport)

    asyncio.run(client.click("button-1"))
    asyncio.run(client.type_text("input-1", "hello"))
    asyncio.run(client.wait(250))
    asyncio.run(client.close())

    assert transport.calls == [
        ("click", "button-1", 10000),
        ("type", "input-1", "hello", 10000),
        ("wait", 250, 10000),
        ("close", 10000),
    ]


def test_playwright_client_denies_when_mode_policy_blocks_server():
    transport = FakePlaywrightTransport()
    client = PlaywrightMCPClient(
        config=PlaywrightClientConfig(mode="coding"),
        guard=guard(),
        transport=transport,
    )

    with pytest.raises(ForbiddenBrowserActionError):
        asyncio.run(client.navigate("https://example.com"))

    assert transport.calls == []


def test_playwright_client_argument_validator_blocks_cookie_script_text():
    transport = FakePlaywrightTransport()
    client = PlaywrightMCPClient(guard=guard(), transport=transport)

    with pytest.raises(ForbiddenBrowserActionError):
        asyncio.run(client.type_text("input", "document.cookie"))

    assert transport.calls == []
