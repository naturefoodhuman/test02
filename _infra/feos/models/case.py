# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""EscalationCase model."""

from __future__ import annotations

from pydantic import Field

from .base import FEOSModel
from .enums import CaseCategory, CaseStatus, Severity
from .ids import utc_now_iso


class CaseOwner(FEOSModel):
    user_id: str = "local_user"
    agent_id: str = "local_agent"


class CaseProblem(FEOSModel):
    user_goal: str
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    failure_signature: str | None = None
    reproduction: str | None = None


class CaseTrigger(FEOSModel):
    type: str = "manual"
    attempts: int = Field(0, ge=0)
    local_confidence: float = Field(0.0, ge=0.0, le=1.0)
    escalation_score: float = Field(0.0, ge=0.0, le=1.0)
    reason: str | None = None


class CaseLinks(FEOSModel):
    evidence_graph_id: str | None = None
    package_ids: list[str] = Field(default_factory=list)
    external_session_ids: list[str] = Field(default_factory=list)
    response_ids: list[str] = Field(default_factory=list)


class CasePolicy(FEOSModel):
    sensitivity_level: str = "internal"
    export_allowed: bool = True
    requires_human_review: bool = True
    redaction_profile: str = "default_strict"


class CaseOutcome(FEOSModel):
    status: str | None = None
    resolution_summary: str | None = None
    root_cause: str | None = None
    fixed_by: str | None = None


class CaseAudit(FEOSModel):
    created_by: str = "feos.manual"
    last_transition_by: str | None = None
    external_exports: list[str] = Field(default_factory=list)


class EscalationCase(FEOSModel):
    id: str
    title: str
    project_id: str = "forge_factory"
    repo_id: str | None = None
    task_id: str | None = None
    status: CaseStatus = CaseStatus.DRAFT
    severity: Severity = Severity.MEDIUM
    category: CaseCategory = CaseCategory.UNKNOWN
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    owner: CaseOwner = Field(default_factory=CaseOwner)
    problem: CaseProblem
    trigger: CaseTrigger = Field(default_factory=CaseTrigger)
    links: CaseLinks = Field(default_factory=CaseLinks)
    policy: CasePolicy = Field(default_factory=CasePolicy)
    outcome: CaseOutcome = Field(default_factory=CaseOutcome)
    audit: CaseAudit = Field(default_factory=CaseAudit)
