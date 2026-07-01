# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Execution planning and outcome models."""

from __future__ import annotations

from pydantic import Field

from .base import FEOSModel
from .ids import utc_now_iso


class ExecutionStep(FEOSModel):
    id: str
    description: str
    command: str | None = None
    requires_approval: bool = True
    status: str = "pending"


class ExecutionPlan(FEOSModel):
    id: str
    case_id: str
    verification_id: str
    steps: list[ExecutionStep] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    approved: bool = False


class Outcome(FEOSModel):
    id: str
    case_id: str
    plan_id: str | None = None
    status: str
    summary: str
    evaluated_at: str = Field(default_factory=utc_now_iso)
    evidence_refs: list[str] = Field(default_factory=list)
