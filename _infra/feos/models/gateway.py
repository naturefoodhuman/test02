# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Gateway models."""

from __future__ import annotations

from pydantic import Field

from .base import FEOSModel
from .enums import GatewayType
from .ids import utc_now_iso


class GatewayCapabilities(FEOSModel):
    gateway: GatewayType
    supports_attachments: bool = False
    supports_structured_output: bool = False
    supports_clipboard: bool = False
    requires_human_review: bool = True
    enabled: bool = False


class HumanAction(FEOSModel):
    type: str
    timestamp: str = Field(default_factory=utc_now_iso)
    actor: str = "human"
    note: str | None = None


class ExternalSession(FEOSModel):
    id: str
    case_id: str
    package_id: str
    gateway: GatewayType = GatewayType.CLIPBOARD
    provider: str = "chatgpt_web"
    started_at: str = Field(default_factory=utc_now_iso)
    ended_at: str | None = None
    human_actions: list[HumanAction] = Field(default_factory=list)
