# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Rule Engine canonical input/output models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

JsonDict = dict[str, Any]


class Verdict(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    ALERT = "alert"


class EvidenceItem(BaseModel):
    rule_id: str
    message: str
    source: str | None = None
    data: JsonDict = Field(default_factory=dict)


class RuleInput(BaseModel):
    domain: str
    payload: JsonDict = Field(default_factory=dict)
    context: JsonDict = Field(default_factory=dict)


class RuleResult(BaseModel):
    domain: str
    verdict: Verdict
    outputs: JsonDict = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    rule_version: str
    reason_code: str

    @classmethod
    def allow(
        cls,
        *,
        domain: str,
        rule_version: str,
        outputs: JsonDict | None = None,
        evidence: list[EvidenceItem] | None = None,
        reason_code: str = "allowed",
    ) -> RuleResult:
        return cls(
            domain=domain,
            verdict=Verdict.ALLOW,
            outputs=outputs or {},
            evidence=evidence or [],
            rule_version=rule_version,
            reason_code=reason_code,
        )

    @classmethod
    def block(
        cls,
        *,
        domain: str,
        rule_version: str,
        reason_code: str,
        evidence: list[EvidenceItem],
        outputs: JsonDict | None = None,
    ) -> RuleResult:
        return cls(
            domain=domain,
            verdict=Verdict.BLOCK,
            outputs=outputs or {},
            evidence=evidence,
            rule_version=rule_version,
            reason_code=reason_code,
        )
