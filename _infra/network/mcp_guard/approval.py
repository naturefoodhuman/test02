# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:20:00

"""High-risk MCP tool human approval flow (E2-C4-S1-T3)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Iterable, Mapping

from .models import MCPToolCall

HIGH_RISK_ACTIONS = (
    "post",
    "comment",
    "dm",
    "direct_message",
    "like",
    "buy",
    "purchase",
    "pay",
    "delete",
    "edit_profile",
    "send_email",
    "submit_form",
    "screenshot",
)


@dataclass(frozen=True)
class ApprovalCheckResult:
    """Result of checking whether a call needs approval."""

    requires_approval: bool
    reason: str = "not_high_risk"
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class HumanApprovalResult:
    """Human approval result for one high-risk call."""

    approved: bool
    prompt: str
    response: str
    reason: str
    check: ApprovalCheckResult


class HighRiskApprovalEngine:
    """Detect high-risk write actions and request strict one-shot approval."""

    def __init__(
        self,
        high_risk_actions: Iterable[str] = HIGH_RISK_ACTIONS,
        input_func: Callable[[str], str] = input,
    ):
        self.high_risk_actions = tuple(action.lower() for action in high_risk_actions)
        self.input_func = input_func

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    @classmethod
    def _iter_arg_strings(cls, value: Any) -> Iterable[str]:
        if isinstance(value, Mapping):
            for key, item in value.items():
                yield str(key)
                yield from cls._iter_arg_strings(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                yield from cls._iter_arg_strings(item)
        elif value is not None:
            yield str(value)

    def check_requires_approval(self, call: MCPToolCall) -> ApprovalCheckResult:
        """Detect high-risk operations by tool name or argument keys/values."""
        candidates = [call.tool_name, f"{call.server_id}.{call.tool_name}"]
        candidates.extend(self._iter_arg_strings(call.args))
        normalized_candidates = [self._normalize(candidate) for candidate in candidates]

        matches: list[str] = []
        for action in self.high_risk_actions:
            normalized_action = self._normalize(action)
            for candidate in normalized_candidates:
                parts = [part for part in candidate.split("_") if part]
                if candidate == normalized_action or normalized_action in parts or normalized_action in candidate:
                    matches.append(action)
                    break

        if matches:
            unique = tuple(dict.fromkeys(matches))
            return ApprovalCheckResult(True, f"high_risk_action:{unique[0]}", unique)
        return ApprovalCheckResult(False)

    def request_approval(self, call: MCPToolCall, check: ApprovalCheckResult | None = None) -> HumanApprovalResult:
        """Ask for strict lowercase yes approval for one call."""
        check = check or self.check_requires_approval(call)
        prompt = (
            "High-risk MCP tool call requires approval. "
            f"mode={call.mode} server={call.server_id} tool={call.tool_name} "
            f"risk={check.reason}. Type 'yes' to approve once: "
        )
        response = self.input_func(prompt).strip()
        approved = response == "yes"
        return HumanApprovalResult(
            approved=approved,
            prompt=prompt,
            response=response,
            reason="human_approved" if approved else "human_rejected",
            check=check,
        )


__all__ = [
    "ApprovalCheckResult",
    "HIGH_RISK_ACTIONS",
    "HighRiskApprovalEngine",
    "HumanApprovalResult",
]
