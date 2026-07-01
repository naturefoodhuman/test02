# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Context package model."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import FEOSModel


class ContextSection(FEOSModel):
    id: str
    title: str
    content: str
    token_estimate: int = Field(0, ge=0)
    source_refs: list[str] = Field(default_factory=list)


class ContextPackage(FEOSModel):
    id: str
    case_id: str
    sections: list[ContextSection] = Field(default_factory=list)
    token_budget: int = Field(24000, ge=1)
    token_estimate: int = Field(0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
