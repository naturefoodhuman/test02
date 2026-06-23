# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:20:00

"""Chrome DevTools MCP read-only client (E8-C3-S1-T1).

The real Chrome DevTools MCP server is installed and exposed through Claude Code
MCP. This Python client is a small, testable boundary object used by future
NetworkWorkflow/private pipelines. It enforces MCPGuard before delegating to an
injected transport (unit tests) or a minimal HTTP fallback for Chrome debug
metadata.

Security boundaries:
- Default mode: private.
- Read-only helpers: get_page_text / get_network_logs.
- screenshot requires MCPGuard approval.
- Storage/cookie helpers are not exposed; read_storage always raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from ..exceptions import BrowserError, ForbiddenBrowserActionError
from ..mcp_guard.guard import MCPGuard
from ..mcp_guard.models import MCPToolCall, PolicyDecision


class ChromeDevToolsTransport(Protocol):
    """Protocol for test/real MCP transport adapters."""

    async def get_page_text(self, url: str | None = None) -> str: ...

    async def get_network_logs(self, url: str | None = None) -> list[dict[str, Any]]: ...

    async def screenshot(self, url: str | None = None) -> bytes: ...


@dataclass(frozen=True)
class ChromeDevToolsClientConfig:
    base_url: str = "http://127.0.0.1:9222"
    server_id: str = "chrome-devtools-private"
    mode: str = "private"
    timeout_seconds: float = 5.0


class ChromeDevToolsMCPClient:
    """Guarded Chrome DevTools MCP client wrapper."""

    def __init__(
        self,
        config: ChromeDevToolsClientConfig | None = None,
        guard: MCPGuard | None = None,
        transport: ChromeDevToolsTransport | None = None,
    ):
        self.config = config or ChromeDevToolsClientConfig()
        self.guard = guard or MCPGuard()
        self.transport = transport

    def _check(self, tool_name: str, args: dict[str, Any] | None = None) -> None:
        decision = self.guard.check(
            MCPToolCall(
                server_id=self.config.server_id,
                tool_name=tool_name,
                args=args or {},
                mode=self.config.mode,  # type: ignore[arg-type]
            )
        )
        if decision.decision != PolicyDecision.ALLOW:
            raise ForbiddenBrowserActionError(
                f"Chrome DevTools tool '{tool_name}' blocked: {decision.reason}"
            )

    async def get_page_text(self, url: str | None = None) -> str:
        """Read page text/snapshot through guarded read-only access."""
        self._check("get_text", {"url": url} if url else {})
        if self.transport is not None:
            return await self.transport.get_page_text(url)
        return await self._fallback_page_summary(url)

    async def get_network_logs(self, url: str | None = None) -> list[dict[str, Any]]:
        """Read network log metadata through guarded read-only access."""
        self._check("get_network_logs", {"url": url} if url else {})
        if self.transport is not None:
            return await self.transport.get_network_logs(url)
        return []

    async def screenshot(self, url: str | None = None) -> bytes:
        """Capture screenshot only when guard approval allows the call."""
        self._check("screenshot", {"url": url} if url else {})
        if self.transport is None:
            raise BrowserError("Screenshot requires Chrome DevTools MCP transport")
        return await self.transport.screenshot(url)

    async def read_storage(self) -> None:
        """Storage/cookie access is forbidden by architecture."""
        raise ForbiddenBrowserActionError("Reading cookies/localStorage/sessionStorage is forbidden")

    async def _fallback_page_summary(self, url: str | None = None) -> str:
        """Minimal HTTP fallback using Chrome /json metadata when no transport is injected."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(f"{self.config.base_url.rstrip('/')}/json")
                response.raise_for_status()
                pages = response.json()
        except Exception as exc:
            raise BrowserError(f"Chrome DevTools endpoint unavailable: {exc}") from exc

        if not isinstance(pages, list):
            return ""
        selected = None
        for page in pages:
            if not isinstance(page, dict):
                continue
            if url is None or page.get("url") == url:
                selected = page
                break
        if selected is None:
            return ""
        title = selected.get("title", "")
        page_url = selected.get("url", "")
        return f"{title}\n{page_url}".strip()


__all__ = ["ChromeDevToolsClientConfig", "ChromeDevToolsMCPClient", "ChromeDevToolsTransport"]
