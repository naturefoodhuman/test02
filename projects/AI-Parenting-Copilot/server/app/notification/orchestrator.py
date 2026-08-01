# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 01:10:00


"""Notification Orchestrator fan-out logic."""

from __future__ import annotations

import asyncio
from typing import Protocol

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.channels.base import DeliveryReceipt, NotificationChannel
from server.app.notification.delivery_repo import InMemoryDeliveryRepository


class DeliveryRepository(Protocol):
    async def add(self, receipt: DeliveryReceipt) -> DeliveryReceipt: ...

    async def list_by_alert(self, alert_id: str) -> list[DeliveryReceipt]: ...


class NotificationOrchestrator:
    """Consumes Alert.level and fans out to configured channels.

    It never creates alert levels. Red/orange use multiple channels by policy.
    """

    def __init__(
        self,
        channels: list[NotificationChannel],
        delivery_repo: DeliveryRepository | None = None,
    ) -> None:
        self.channels = {channel.name: channel for channel in channels}
        self.delivery_repo = delivery_repo or InMemoryDeliveryRepository()

    def channels_for(self, alert: AlertRecord) -> list[NotificationChannel]:
        if alert.level in {AlertLevel.RED, AlertLevel.ORANGE}:
            names = ["fcm", "mac_speaker", "app_fullscreen"]
            if "camera_speaker" in self.channels:
                names.append("camera_speaker")
            return [self.channels[name] for name in names if name in self.channels]
        if alert.level == AlertLevel.YELLOW:
            return [
                channel
                for name, channel in self.channels.items()
                if name in {"fcm", "app_fullscreen"}
            ]
        return [channel for name, channel in self.channels.items() if name == "app_fullscreen"]

    async def dispatch(self, alert: AlertRecord) -> list[DeliveryReceipt]:
        selected = self.channels_for(alert)
        receipts = await asyncio.gather(*(channel.send(alert) for channel in selected))
        for receipt in receipts:
            await self.delivery_repo.add(receipt)
        return list(receipts)
