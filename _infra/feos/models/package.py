# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Escalation package model."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import FEOSModel
from .enums import GatewayType


class EscalationPackage(FEOSModel):
    id: str
    case_id: str
    context_package_id: str
    gateway: GatewayType = GatewayType.CLIPBOARD
    provider: str = "chatgpt_web"
    renderer_profile: str = "generic_markdown"
    rendered_ref: str | None = None
    manifest_ref: str | None = None
    evidence_index_ref: str | None = None
    redaction_report_ref: str | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
