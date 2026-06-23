# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:16:58

"""Playwright MCP client boundary (E7-C2-S1-T1).

This module provides a guarded, transport-injected client for public browser
automation. It does not launch Playwright itself; real transport wiring belongs
to the MCP runtime. Unit tests use a fake transport.

Security:
- default server_id: playwright-public
- default mode: research
- every tool call goes through MCPGuard first
- no arbitrary shell / storage / cookie export helpers are exposed
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..exceptions import BrowserError, ForbiddenBrowserActionError
from ..mcp_guard.guard import MCPGuard
from ..mcp_guard.models import MCPToolCall, PolicyDecision


class PlaywrightTransport(Protocol):
    async def navigate(self, url: str, timeout_ms: int) -> dict[str, Any]: ...

    async def snapshot(self, timeout_ms: int) -> dict[str, Any]: ...

    async def click(self, ref: str, timeout_ms: int) -> dict[str, Any]: ...

    async def type_text(self, ref: str, text: str, timeout_ms: int) -> dict[str, Any]: ...

    async def wait(self, ms: int, timeout_ms: int) -> dict[str, Any]: ...

    async def close(self, timeout_ms: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class PlaywrightClientConfig:
    server_id: str = "playwright-public"
    mode: str = "research"
    navigate_timeout_ms: int = 30_000
    action_timeout_ms: int = 10_000


class PlaywrightMCPClient:
    """Guarded client facade for Playwright MCP tools."""

    def __init__(
        self,
        config: PlaywrightClientConfig | None = None,
        guard: MCPGuard | None = None,
        transport: PlaywrightTransport | None = None,
    ):
        self.config = config or PlaywrightClientConfig()
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
            raise ForbiddenBrowserActionError(f"Playwright tool '{tool_name}' blocked: {decision.reason}")

    def _require_transport(self) -> PlaywrightTransport:
        if self.transport is None:
            raise BrowserError("Playwright MCP transport is not configured")
        return self.transport

    async def navigate(self, url: str) -> dict[str, Any]:
        self._check("navigate", {"url": url})
        return await self._require_transport().navigate(url, self.config.navigate_timeout_ms)

    async def snapshot(self) -> dict[str, Any]:
        self._check("snapshot")
        return await self._require_transport().snapshot(self.config.action_timeout_ms)

    async def click(self, ref: str) -> dict[str, Any]:
        self._check("click", {"ref": ref})
        return await self._require_transport().click(ref, self.config.action_timeout_ms)

    async def type_text(self, ref: str, text: str) -> dict[str, Any]:
        self._check("type", {"ref": ref, "text": text})
        return await self._require_transport().type_text(ref, text, self.config.action_timeout_ms)

    async def wait(self, ms: int) -> dict[str, Any]:
        self._check("wait", {"ms": ms})
        return await self._require_transport().wait(ms, self.config.action_timeout_ms)

    async def close(self) -> dict[str, Any]:
        self._check("close")
        return await self._require_transport().close(self.config.action_timeout_ms)


__all__ = ["PlaywrightClientConfig", "PlaywrightMCPClient", "PlaywrightTransport"]
