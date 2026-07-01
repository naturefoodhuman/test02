# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Knowledge distillation models."""

from __future__ import annotations

from pydantic import Field

from .base import FEOSModel
from .enums import KnowledgeCandidateStatus
from .ids import utc_now_iso


class KnowledgeCandidate(FEOSModel):
    id: str
    case_id: str
    title: str
    content: str
    status: KnowledgeCandidateStatus = KnowledgeCandidateStatus.CAPTURED
    source_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    tags: list[str] = Field(default_factory=list)
