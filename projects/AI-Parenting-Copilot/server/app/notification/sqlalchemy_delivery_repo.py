# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 16:05:00


"""SQLAlchemy alert delivery receipt repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models import AlertDelivery as ORMAlertDelivery
from server.app.notification.channels.base import DeliveryReceipt


class SQLAlchemyDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, receipt: DeliveryReceipt) -> DeliveryReceipt:
        self.session.add(
            ORMAlertDelivery(
                id=receipt.id,
                alert_id=receipt.alert_id,
                channel=receipt.channel,
                target=receipt.target,
                status=receipt.status,
                sent_at=receipt.sent_at,
                receipt=receipt.receipt,
            )
        )
        await self.session.flush()
        return receipt

    async def list_by_alert(self, alert_id: str) -> list[DeliveryReceipt]:
        rows = await self.session.scalars(
            select(ORMAlertDelivery).where(ORMAlertDelivery.alert_id == alert_id)
        )
        return [
            DeliveryReceipt(
                id=row.id,
                alert_id=row.alert_id,
                channel=row.channel,
                target=row.target,
                status=row.status,
                sent_at=row.sent_at.isoformat() if row.sent_at else "",
                receipt=row.receipt,
            )
            for row in rows
        ]
