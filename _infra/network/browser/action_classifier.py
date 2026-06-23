# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:05:00

"""Browser action risk classifier (E7-C5-S1-T1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Mapping

READ_ONLY_ACTIONS = {"snapshot", "read", "get_text", "get_network_logs", "extract", "close"}
LOW_RISK_ACTIONS = {"open", "navigate", "wait", "scroll", "hover"}
HIGH_RISK_ACTIONS = {
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
    "checkout",
    "upload",
}
HIGH_RISK_HINTS = {
    "submit",
    "send",
    "publish",
    "confirm",
    "purchase",
    "checkout",
    "payment",
    "password",
    "delete",
    "remove",
}


class BrowserActionRisk(str, Enum):
    READ_ONLY = "read_only"
    LOW_RISK = "low_risk"
    HIGH_RISK = "high_risk"


@dataclass(frozen=True)
class BrowserAction:
    """Browser action proposed by an agent/orchestrator."""

    action_type: str
    target: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    page_url: str | None = None
    account: str | None = None


@dataclass(frozen=True)
class BrowserActionRiskResult:
    """Risk classification result."""

    risk: BrowserActionRisk
    reason: str
    approval_required: bool
    matched_terms: tuple[str, ...] = ()
    diff_preview: Mapping[str, Any] = field(default_factory=dict)


class BrowserActionClassifier:
    """Classify browser actions into read_only / low_risk / high_risk."""

    def __init__(
        self,
        high_risk_actions: set[str] | None = None,
        high_risk_hints: set[str] | None = None,
    ):
        self.high_risk_actions = {self._normalize(x) for x in (high_risk_actions or HIGH_RISK_ACTIONS)}
        self.high_risk_hints = {self._normalize(x) for x in (high_risk_hints or HIGH_RISK_HINTS)}

    @staticmethod
    def _normalize(value: str | None) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")

    @classmethod
    def _iter_strings(cls, value: Any):
        if isinstance(value, Mapping):
            for key, item in value.items():
                yield str(key)
                yield from cls._iter_strings(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                yield from cls._iter_strings(item)
        elif value is not None:
            yield str(value)

    @staticmethod
    def _contains_term(candidate: str, term: str) -> bool:
        parts = [part for part in candidate.split("_") if part]
        return candidate == term or term in parts or term in candidate

    def classify(self, action: BrowserAction) -> BrowserActionRiskResult:
        normalized_action = self._normalize(action.action_type)
        candidates = [normalized_action, self._normalize(action.target)]
        candidates.extend(self._normalize(value) for value in self._iter_strings(action.payload))

        matched = []
        for term in sorted(self.high_risk_actions | self.high_risk_hints):
            if any(self._contains_term(candidate, term) for candidate in candidates):
                matched.append(term)

        if normalized_action in self.high_risk_actions or matched:
            return BrowserActionRiskResult(
                risk=BrowserActionRisk.HIGH_RISK,
                reason=f"high_risk:{matched[0] if matched else normalized_action}",
                approval_required=True,
                matched_terms=tuple(dict.fromkeys(matched or [normalized_action])),
                diff_preview=self._diff_preview(action),
            )

        if normalized_action in READ_ONLY_ACTIONS:
            return BrowserActionRiskResult(
                risk=BrowserActionRisk.READ_ONLY,
                reason="read_only_action",
                approval_required=False,
                diff_preview=self._diff_preview(action),
            )

        return BrowserActionRiskResult(
            risk=BrowserActionRisk.LOW_RISK,
            reason="low_risk_action",
            approval_required=False,
            diff_preview=self._diff_preview(action),
        )

    @staticmethod
    def _diff_preview(action: BrowserAction) -> dict[str, Any]:
        return {
            "action_type": action.action_type,
            "target": action.target,
            "page_url": action.page_url,
            "account": action.account,
            "payload_keys": sorted(str(key) for key in action.payload.keys()),
        }


def classify_action(action: BrowserAction) -> BrowserActionRiskResult:
    """Convenience function."""
    return BrowserActionClassifier().classify(action)


__all__ = [
    "BrowserAction",
    "BrowserActionClassifier",
    "BrowserActionRisk",
    "BrowserActionRiskResult",
    "classify_action",
]
