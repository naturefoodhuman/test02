# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pydantic import Field

from _infra.feos.adapters.privacy_adapter import PrivacyAdapter
from _infra.feos.models.base import FEOSModel


class PolicyResult(FEOSModel):
    allowed: bool
    redacted_text: str = ""
    requires_human_review: bool = True
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    redaction_report: dict = Field(default_factory=dict)


class PolicyEngine:
    def __init__(self, privacy: PrivacyAdapter | None = None, allowed_gateways: set[str] | None = None, token_budget: int = 24000):
        self.privacy = privacy or PrivacyAdapter()
        self.allowed_gateways = allowed_gateways or {"clipboard"}
        self.token_budget = token_budget

    def check_export(self, text: str, gateway: str = "clipboard", estimated_tokens: int = 0) -> PolicyResult:
        if gateway not in self.allowed_gateways:
            return PolicyResult(allowed=False, errors=[f"gateway disabled: {gateway}"])
        redaction = self.privacy.redact(text)
        if redaction.blocked:
            return PolicyResult(allowed=False, errors=["privacy block"], redaction_report=redaction.to_dict())
        warnings = []
        if estimated_tokens > self.token_budget:
            warnings.append("token budget exceeded")
        return PolicyResult(
            allowed=True,
            redacted_text=redaction.text,
            requires_human_review=True,
            warnings=warnings,
            redaction_report=redaction.to_dict(),
        )
