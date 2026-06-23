# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:20:00

"""Unit tests for ChromeDevToolsMCPClient (E8-C3-S1-T1)."""

import pytest

from _infra.network.exceptions import BrowserError, ForbiddenBrowserActionError
from _infra.network.mcp_guard.approval import HighRiskApprovalEngine
from _infra.network.mcp_guard.guard import MCPGuard
from _infra.network.mcp_guard.mode_policy import ModePolicyEngine
from _infra.network.mcp_guard.models import PolicyDecision
from _infra.network.browser.chrome_devtools_client import ChromeDevToolsMCPClient


class FakeTransport:
    def __init__(self):
        self.calls = []

    async def get_page_text(self, url=None):
        self.calls.append(("get_page_text", url))
        return "Alice private page text"

    async def get_network_logs(self, url=None):
        self.calls.append(("get_network_logs", url))
        return [{"url": "https://github.com", "status": 200}]

    async def screenshot(self, url=None):
        self.calls.append(("screenshot", url))
        return b"png"


def guard_with_approval(response: str = "no") -> MCPGuard:
    return MCPGuard(
        mode_policy=ModePolicyEngine.from_config(),
        approval_engine=HighRiskApprovalEngine(input_func=lambda _prompt: response),
        default_decision=PolicyDecision.ALLOW,
    )


@pytest.mark.parametrize("method_name", ["get_page_text", "get_network_logs"])
async def _call(client, method_name):
    return await getattr(client, method_name)("https://github.com")


def test_get_page_text_allowed_with_private_mode():
    transport = FakeTransport()
    client = ChromeDevToolsMCPClient(guard=guard_with_approval(), transport=transport)

    import asyncio

    text = asyncio.run(client.get_page_text("https://github.com"))

    assert text == "Alice private page text"
    assert transport.calls == [("get_page_text", "https://github.com")]


def test_get_network_logs_allowed_read_only():
    transport = FakeTransport()
    client = ChromeDevToolsMCPClient(guard=guard_with_approval(), transport=transport)

    import asyncio

    logs = asyncio.run(client.get_network_logs("https://github.com"))

    assert logs == [{"url": "https://github.com", "status": 200}]


def test_screenshot_requires_human_approval():
    transport = FakeTransport()
    denied = ChromeDevToolsMCPClient(guard=guard_with_approval("no"), transport=transport)
    approved = ChromeDevToolsMCPClient(guard=guard_with_approval("yes"), transport=transport)

    import asyncio

    with pytest.raises(ForbiddenBrowserActionError):
        asyncio.run(denied.screenshot("https://github.com"))

    assert asyncio.run(approved.screenshot("https://github.com")) == b"png"


def test_storage_access_is_forbidden_even_with_transport():
    client = ChromeDevToolsMCPClient(guard=guard_with_approval("yes"), transport=FakeTransport())

    import asyncio

    with pytest.raises(ForbiddenBrowserActionError):
        asyncio.run(client.read_storage())


def test_screenshot_without_transport_raises_browser_error_after_approval():
    client = ChromeDevToolsMCPClient(guard=guard_with_approval("yes"), transport=None)

    import asyncio

    with pytest.raises(BrowserError):
        asyncio.run(client.screenshot("https://github.com"))
