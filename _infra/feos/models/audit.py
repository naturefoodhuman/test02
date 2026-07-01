# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Audit records for FEOS artifacts and exports."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import FEOSModel
from .ids import utc_now_iso


class AuditRecord(FEOSModel):
    id: str
    case_id: str
    operation: str
    actor: str = "feos"
    timestamp: str = Field(default_factory=utc_now_iso)
    content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
