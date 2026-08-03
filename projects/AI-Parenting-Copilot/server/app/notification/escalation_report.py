# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:12:00

"""Deterministic red-alert escalation simulation report.

This is a dev/E2E substitute: it uses fake channels and the real
EscalationStateMachine/NotificationOrchestrator code path. It never sends real FCM,
plays audio, or bypasses Notification Orchestrator.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.channels.base import NotificationChannel
from server.app.notification.channels.fake import (
    FakeAppFullscreenChannel,
    FakeCameraSpeakerChannel,
    FakeFCMChannel,
    FakeMacSpeakerChannel,
    FakeNotificationChannel,
)
from server.app.notification.escalation import EscalationPolicy, EscalationStateMachine
from server.app.notification.orchestrator import NotificationOrchestrator


@dataclass(frozen=True, slots=True)
class RedAlertEscalationReport:
    alert_id: str
    stages: tuple[str, ...]
    receipt_channels: tuple[str, ...]
    receipt_statuses: tuple[str, ...]
    trigger_only_payloads: bool
    cancelled_channels: tuple[str, ...]
    acknowledged: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


async def simulate_red_alert_escalation(
    *,
    repeat_seconds: int = 60,
    escalate_seconds: int = 90,
    ack_after_seconds: int | None = 90,
) -> RedAlertEscalationReport:
    fake_channels: list[FakeNotificationChannel] = [
        FakeFCMChannel(),
        FakeMacSpeakerChannel(),
        FakeAppFullscreenChannel(),
        FakeCameraSpeakerChannel(),
    ]
    channels: list[NotificationChannel] = list(fake_channels)
    machine = EscalationStateMachine(
        NotificationOrchestrator(channels),
        policy=EscalationPolicy(repeat_seconds=repeat_seconds, escalate_seconds=escalate_seconds),
    )
    alert = AlertRecord(
        baby_id="baby-red-sim",
        family_id="family-red-sim",
        level=AlertLevel.RED,
        type="triage",
        evidence={"source": "red_alert_simulation"},
        recommended_action="open app for details",
    )
    session = await machine.start(alert)
    await machine.advance(session, repeat_seconds)
    await machine.advance(session, max(0, escalate_seconds - repeat_seconds))
    if ack_after_seconds is not None:
        await machine.ack(session, ack_by="sim-parent", device_id="sim-phone")
    payloads = [receipt.receipt.get("payload", {}) for receipt in session.receipts]
    trigger_only = all(
        isinstance(payload, dict) and set(payload.keys()) <= {"alert_id", "level", "type"}
        for payload in payloads
        if payload
    )
    cancelled = sorted(channel.name for channel in fake_channels if alert.id in channel.cancelled)
    return RedAlertEscalationReport(
        alert_id=alert.id,
        stages=tuple(session.stages),
        receipt_channels=tuple(receipt.channel for receipt in session.receipts),
        receipt_statuses=tuple(receipt.status for receipt in session.receipts),
        trigger_only_payloads=trigger_only,
        cancelled_channels=tuple(cancelled),
        acknowledged=session.acknowledged,
    )
