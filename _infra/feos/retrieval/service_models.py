# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pydantic import Field

from _infra.feos.models.base import FEOSModel


class SimilarityResult(FEOSModel):
    case_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str = ""
