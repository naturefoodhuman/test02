# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.policy.redaction import RegexRedactor
from _infra.feos.ports.policy import PrivacyScanResult, RedactionResult


class PrivacyAdapter:
    def __init__(self, gateway=None, fallback: RegexRedactor | None = None):
        self.gateway = gateway
        self.fallback = fallback or RegexRedactor()

    def redact(self, text: str, policy_profile: str = "default_strict") -> RedactionResult:
        # Full network PrivacyGateway integration is intentionally deferred; fallback is deterministic.
        return self.fallback.redact(text)

    def scan(self, text: str, policy_profile: str = "default_strict") -> PrivacyScanResult:
        result = self.redact(text, policy_profile)
        return PrivacyScanResult(blocked=result.blocked, detections=result.detections, reason="blocked" if result.blocked else None)
