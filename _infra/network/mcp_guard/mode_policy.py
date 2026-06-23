# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:02:00

"""Mode permission policy engine for MCP Guard (E2-C4-S1-T2)."""

from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch
from pathlib import Path
from typing import Any, Mapping

import yaml

from .models import MCPMode, MCPToolCall

DEFAULT_MODE_POLICY_PATH = Path("config/mode_policies.yaml")


@dataclass(frozen=True)
class ModePolicy:
    """Policy for one Claude Code mode."""

    allowed_servers: list[str] = field(default_factory=list)
    denied_servers: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    forbidden_tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModePolicyResult:
    """Result of evaluating a mode policy."""

    allowed: bool
    reason: str
    mode: MCPMode
    server_id: str
    tool_name: str


class ModePolicyEngine:
    """Config-driven MCP mode permission policy engine."""

    def __init__(self, policies: Mapping[str, ModePolicy]):
        self.policies = dict(policies)

    @classmethod
    def from_config(cls, path: str | Path = DEFAULT_MODE_POLICY_PATH) -> "ModePolicyEngine":
        config_path = Path(path)
        if not config_path.exists():
            return cls({})
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        modes = data.get("modes", {}) if isinstance(data, Mapping) else {}
        policies: dict[str, ModePolicy] = {}
        for mode, raw in modes.items():
            raw = raw or {}
            policies[str(mode)] = ModePolicy(
                allowed_servers=list(raw.get("allowed_servers", []) or []),
                denied_servers=list(raw.get("denied_servers", raw.get("forbidden_servers", [])) or []),
                allowed_tools=list(raw.get("allowed_tools", []) or []),
                forbidden_tools=list(raw.get("forbidden_tools", []) or []),
            )
        return cls(policies)

    @staticmethod
    def _matches(value: str, patterns: list[str]) -> bool:
        return any(pattern == "*" or fnmatch.fnmatchcase(value, pattern) for pattern in patterns)

    @staticmethod
    def _tool_matches(server_id: str, tool_name: str, patterns: list[str]) -> bool:
        namespaced = f"{server_id}.{tool_name}"
        return ModePolicyEngine._matches(tool_name, patterns) or ModePolicyEngine._matches(namespaced, patterns)

    def evaluate(self, call: MCPToolCall) -> ModePolicyResult:
        policy = self.policies.get(call.mode)
        if policy is None:
            return ModePolicyResult(False, f"mode_policy_missing:{call.mode}", call.mode, call.server_id, call.tool_name)

        if self._matches(call.server_id, policy.denied_servers):
            return ModePolicyResult(False, f"server_denied:{call.server_id}", call.mode, call.server_id, call.tool_name)

        if policy.allowed_servers and not self._matches(call.server_id, policy.allowed_servers):
            return ModePolicyResult(False, f"server_not_allowed:{call.server_id}", call.mode, call.server_id, call.tool_name)

        if self._tool_matches(call.server_id, call.tool_name, policy.forbidden_tools):
            return ModePolicyResult(False, f"tool_forbidden:{call.tool_name}", call.mode, call.server_id, call.tool_name)

        if policy.allowed_tools and not self._tool_matches(call.server_id, call.tool_name, policy.allowed_tools):
            return ModePolicyResult(False, f"tool_not_allowed:{call.tool_name}", call.mode, call.server_id, call.tool_name)

        return ModePolicyResult(True, "mode_policy_allow", call.mode, call.server_id, call.tool_name)

    def check_mode_policy(self, call: MCPToolCall) -> bool:
        """Compatibility helper required by TASK_BACKLOG."""
        return self.evaluate(call).allowed


__all__ = ["DEFAULT_MODE_POLICY_PATH", "ModePolicy", "ModePolicyEngine", "ModePolicyResult"]
