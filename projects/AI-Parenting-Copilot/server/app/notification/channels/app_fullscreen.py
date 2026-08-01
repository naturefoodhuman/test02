# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 00:57:00

"""App fullscreen intent trigger channel."""

from __future__ import annotations

from server.app.notification.alert_repo import AlertRecord
from server.app.notification.channels.base import DeliveryReceipt


class AppFullscreenChannel:
    name = "app_fullscreen"

    def __init__(self) -> None:
        self.cancelled: list[str] = []

    async def send(self, alert: AlertRecord) -> DeliveryReceipt:
        return DeliveryReceipt(
            alert_id=alert.id,
            channel=self.name,
            status="queued",
            receipt={
                "payload": {
                    "alert_id": alert.id,
                    "level": alert.level.value,
                    "type": alert.type,
                    "fullscreen": True,
                }
            },
        )

    async def cancel(self, alert: AlertRecord) -> None:
        self.cancelled.append(alert.id)
