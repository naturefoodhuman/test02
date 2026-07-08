# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 05:55:00


"""Notification channel protocol and delivery receipt."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid
from server.app.notification.alert_repo import AlertRecord


class DeliveryReceipt(BaseModel):
    id: str = Field(default_factory=new_ulid)
    alert_id: str
    channel: str
    target: str | None = None
    status: str
    sent_at: str = Field(default_factory=lambda: utc_now().isoformat())
    receipt: dict[str, object] = Field(default_factory=dict)


class NotificationChannel(Protocol):
    name: str

    async def send(self, alert: AlertRecord) -> DeliveryReceipt: ...
