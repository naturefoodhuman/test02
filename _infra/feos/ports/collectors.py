# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Evidence collector protocol and request/result models."""

from __future__ import annotations

from typing import Protocol

from pydantic import Field

from _infra.feos.models.base import FEOSModel
from _infra.feos.models.enums import EvidenceType


class EvidenceCollectionRequest(FEOSModel):
    case_id: str
    paths: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    task_metadata: dict = Field(default_factory=dict)
    user_input: str | None = None
    previous_attempts: list[str] = Field(default_factory=list)
    agent_plan: str | None = None


class CollectedEvidence(FEOSModel):
    collector_id: str
    evidence_type: EvidenceType = EvidenceType.OTHER
    raw_content: str
    subtype: str | None = None
    origin: str = "collector"
    metadata: dict = Field(default_factory=dict)
    required: bool = False


class EvidenceCollector(Protocol):
    collector_id: str
    required: bool

    def can_collect(self, request: EvidenceCollectionRequest) -> bool: ...

    def collect(self, request: EvidenceCollectionRequest) -> list[CollectedEvidence]: ...
