# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Verification models."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import FEOSModel
from .enums import VerificationStatus


class VerificationCheckResult(FEOSModel):
    check_id: str
    status: VerificationStatus = VerificationStatus.PENDING
    summary: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class VerificationResult(FEOSModel):
    id: str
    case_id: str
    parsed_response_id: str
    status: VerificationStatus = VerificationStatus.PENDING
    checks: list[VerificationCheckResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
