# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 05:55:00


"""Alert repository and state transitions."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.common.errors import NotFoundError
from server.app.common.ids import new_ulid
from server.app.observability.audit import AuditActor, AuditRecord, AuditSink


class AlertLevel(StrEnum):
    GRAY = "gray"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class AlertStatus(StrEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class FeedbackType(StrEnum):
    USEFUL = "useful"
    FALSE_POSITIVE = "false_positive"
    TOO_SENSITIVE = "too_sensitive"
    ALREADY_KNOWN = "already_known"
    IGNORED = "ignored"


class AlertRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    baby_id: str
    family_id: str
    level: AlertLevel
    type: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str | None = None
    status: AlertStatus = AlertStatus.ACTIVE
    ack_by: str | None = None
    ack_device_id: str | None = None
    ack_at: str | None = None
    feedback: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = Field(default_factory=lambda: utc_now().isoformat())


class CreateAlertRequest(BaseModel):
    baby_id: str
    family_id: str
    level: AlertLevel
    type: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str | None = None


class AckAlertRequest(BaseModel):
    ack_by: str
    device_id: str | None = None


class FeedbackRequest(BaseModel):
    feedback: FeedbackType
    note: str | None = None


class InMemoryAlertRepository:
    """Dev in-memory alert store until DB-backed repository lands."""

    def __init__(self, audit_sink: AuditSink | None = None) -> None:
        self.alerts: dict[str, AlertRecord] = {}
        self.audit_sink = audit_sink

    async def create(self, request: CreateAlertRequest) -> AlertRecord:
        alert = AlertRecord(**request.model_dump())
        self.alerts[alert.id] = alert
        await self._audit("alert.create", alert)
        return alert

    async def get(self, alert_id: str) -> AlertRecord:
        alert = self.alerts.get(alert_id)
        if alert is None:
            raise NotFoundError("Alert not found", evidence={"alert_id": alert_id})
        return alert

    async def list_active(self, family_id: str | None = None) -> list[AlertRecord]:
        alerts = [alert for alert in self.alerts.values() if alert.status == AlertStatus.ACTIVE]
        if family_id is not None:
            alerts = [alert for alert in alerts if alert.family_id == family_id]
        return sorted(alerts, key=lambda alert: alert.created_at, reverse=True)

    async def ack(self, alert_id: str, request: AckAlertRequest) -> AlertRecord:
        alert = await self.get(alert_id)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.ack_by = request.ack_by
        alert.ack_device_id = request.device_id
        alert.ack_at = utc_now().isoformat()
        alert.updated_at = alert.ack_at
        await self._audit("alert.ack", alert)
        return alert

    async def feedback(self, alert_id: str, request: FeedbackRequest) -> AlertRecord:
        alert = await self.get(alert_id)
        alert.feedback = {"type": request.feedback.value, "note": request.note}
        alert.updated_at = utc_now().isoformat()
        await self._audit("alert.feedback", alert)
        return alert

    async def _audit(self, action: str, alert: AlertRecord) -> None:
        if self.audit_sink is None:
            return
        await self.audit_sink.record(
            AuditRecord(
                actor=AuditActor(actor_kind="system"),
                action=action,
                resource=f"alert:{alert.id}",
                after=alert.model_dump(mode="json"),
            )
        )
