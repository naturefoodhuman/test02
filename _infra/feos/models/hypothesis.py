# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Hypothesis model."""

from __future__ import annotations

from pydantic import Field

from .base import FEOSModel
from .enums import HypothesisStatus


class Hypothesis(FEOSModel):
    id: str
    case_id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    supports: list[str] = Field(default_factory=list)
    refutes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
