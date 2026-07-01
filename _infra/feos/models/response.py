# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""External response and parsed response models."""

from __future__ import annotations

from pydantic import Field

from .base import FEOSModel
from .ids import utc_now_iso


class ExternalResponse(FEOSModel):
    id: str
    case_id: str
    session_id: str
    raw_ref: str
    content_hash: str
    imported_at: str = Field(default_factory=utc_now_iso)
    provider: str | None = None


class ParsedClaim(FEOSModel):
    id: str
    text: str
    evidence_refs: list[str] = Field(default_factory=list)


class Recommendation(FEOSModel):
    id: str
    text: str
    risk_level: str = "medium"
    requires_verification: bool = True


class ParsedResponse(FEOSModel):
    id: str
    case_id: str
    response_id: str
    claims: list[ParsedClaim] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
