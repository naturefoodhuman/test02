# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-23 11:02:00

"""Core MCP Guard data models (E2-C4-S1-T1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Mapping, Optional

MCPMode = Literal["coding", "research", "private"]


class PolicyDecision(str, Enum):
    """Guard decision values."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class MCPToolCall:
    """A tool call request passed to the PreToolUse guard."""

    server_id: str
    tool_name: str
    args: Mapping[str, Any] = field(default_factory=dict)
    mode: MCPMode = "research"
    schema: Mapping[str, Any] | None = None
    trace_id: Optional[str] = None

    def __post_init__(self):
        if self.mode not in {"coding", "research", "private"}:
            raise ValueError("mode must be one of: coding, research, private")
        if not self.server_id:
            raise ValueError("server_id is required")
        if not self.tool_name:
            raise ValueError("tool_name is required")


@dataclass(frozen=True)
class MCPToolResult:
    """A sanitized MCP tool execution result placeholder for future hooks."""

    success: bool
    result: Any = None
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardDecision:
    """Decision returned by MCPGuard.check()."""

    decision: PolicyDecision
    reason: str
    server_id: str
    tool_name: str
    mode: MCPMode
    audit_event_id: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOW

    @property
    def denied(self) -> bool:
        return self.decision == PolicyDecision.DENY

    @property
    def requires_approval(self) -> bool:
        return self.decision == PolicyDecision.REQUIRE_APPROVAL


__all__ = [
    "GuardDecision",
    "MCPMode",
    "MCPToolCall",
    "MCPToolResult",
    "PolicyDecision",
]
