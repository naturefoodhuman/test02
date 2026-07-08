# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 05:55:00


"""Delivery receipt repository."""

from __future__ import annotations

from server.app.notification.channels.base import DeliveryReceipt


class InMemoryDeliveryRepository:
    def __init__(self) -> None:
        self.receipts: list[DeliveryReceipt] = []

    async def add(self, receipt: DeliveryReceipt) -> DeliveryReceipt:
        self.receipts.append(receipt)
        return receipt

    async def list_by_alert(self, alert_id: str) -> list[DeliveryReceipt]:
        return [receipt for receipt in self.receipts if receipt.alert_id == alert_id]
