# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Evidence model."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import FEOSModel
from .enums import EvidenceType
from .ids import utc_now_iso


class EvidenceSource(FEOSModel):
    collector: str
    origin: str
    file: str | None = None
    line_start: int | None = None
    line_end: int | None = None


class EvidenceContent(FEOSModel):
    raw_ref: str
    text_preview: str | None = None
    normalized: dict[str, Any] = Field(default_factory=dict)


class EvidenceQuality(FEOSModel):
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    freshness: float = Field(1.0, ge=0.0, le=1.0)
    completeness: float = Field(1.0, ge=0.0, le=1.0)


class EvidenceSecurity(FEOSModel):
    sensitivity: str = "internal"
    contains_secret: bool = False
    contains_pii: bool = False
    redaction_status: str = "not_needed"


class EvidenceRelations(FEOSModel):
    supports: list[str] = Field(default_factory=list)
    refutes: list[str] = Field(default_factory=list)
    relates: list[str] = Field(default_factory=list)


class Evidence(FEOSModel):
    id: str
    case_id: str
    type: EvidenceType = EvidenceType.OTHER
    subtype: str | None = None
    source: EvidenceSource
    content: EvidenceContent
    metadata: dict[str, Any] = Field(default_factory=lambda: {"timestamp": utc_now_iso()})
    quality: EvidenceQuality = Field(default_factory=EvidenceQuality)
    security: EvidenceSecurity = Field(default_factory=EvidenceSecurity)
    relations: EvidenceRelations = Field(default_factory=EvidenceRelations)
