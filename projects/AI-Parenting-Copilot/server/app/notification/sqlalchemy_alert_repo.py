# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 15:20:00


"""SQLAlchemy Alert repository adapter."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.common.errors import NotFoundError
from server.app.models import Alert as ORMAlert
from server.app.notification.alert_repo import (
    AckAlertRequest,
    AlertLevel,
    AlertRecord,
    AlertStatus,
    CreateAlertRequest,
    FeedbackRequest,
)


class SQLAlchemyAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, request: CreateAlertRequest) -> AlertRecord:
        record = AlertRecord(**request.model_dump())
        self.session.add(
            ORMAlert(
                id=record.id,
                baby_id=record.baby_id,
                family_id=record.family_id,
                level=record.level.value,
                type=record.type,
                evidence=record.evidence,
                recommended_action=record.recommended_action,
                status=record.status.value,
                feedback=record.feedback,
            )
        )
        await self.session.flush()
        return record

    async def get(self, alert_id: str) -> AlertRecord:
        row = await self.session.scalar(select(ORMAlert).where(ORMAlert.id == alert_id))
        if row is None:
            raise NotFoundError("Alert not found", evidence={"alert_id": alert_id})
        return self._to_domain(row)

    async def list_active(self, family_id: str | None = None) -> list[AlertRecord]:
        stmt = select(ORMAlert).where(ORMAlert.status == AlertStatus.ACTIVE.value)
        if family_id is not None:
            stmt = stmt.where(ORMAlert.family_id == family_id)
        rows = await self.session.scalars(stmt.order_by(ORMAlert.created_at.desc()))
        return [self._to_domain(row) for row in rows]

    async def ack(self, alert_id: str, request: AckAlertRequest) -> AlertRecord:
        row = await self.session.scalar(select(ORMAlert).where(ORMAlert.id == alert_id))
        if row is None:
            raise NotFoundError("Alert not found", evidence={"alert_id": alert_id})
        row.status = AlertStatus.ACKNOWLEDGED.value
        row.ack_by = request.ack_by
        row.ack_at = utc_now()
        await self.session.flush()
        return self._to_domain(row)

    async def feedback(self, alert_id: str, request: FeedbackRequest) -> AlertRecord:
        row = await self.session.scalar(select(ORMAlert).where(ORMAlert.id == alert_id))
        if row is None:
            raise NotFoundError("Alert not found", evidence={"alert_id": alert_id})
        row.feedback = {"type": request.feedback.value, "note": request.note}
        await self.session.flush()
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: ORMAlert) -> AlertRecord:
        return AlertRecord(
            id=row.id,
            baby_id=row.baby_id,
            family_id=row.family_id,
            level=AlertLevel(row.level),
            type=row.type,
            evidence=row.evidence,
            recommended_action=row.recommended_action,
            status=AlertStatus(row.status),
            ack_by=row.ack_by,
            ack_at=row.ack_at.isoformat() if row.ack_at else None,
            feedback=row.feedback,
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
        )
