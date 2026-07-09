# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


"""APC-T057 fake red alert delivery E2E regression."""
from __future__ import annotations

import pytest

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.escalation import EscalationPolicy, EscalationStateMachine
from server.app.notification.orchestrator import NotificationOrchestrator
from tests.fakes import build_fake_notification_channels


@pytest.mark.asyncio
async def test_fake_red_alert_delivery_escalates_and_ack_cancels() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")
    channels = build_fake_notification_channels()
    machine = EscalationStateMachine(
        NotificationOrchestrator(channels),
        policy=EscalationPolicy(repeat_seconds=60, escalate_seconds=90),
    )

    session = await machine.start(alert)
    await machine.advance(session, 90)
    await machine.ack(session, ack_by="u1")

    assert "initial_fanout" in session.stages
    assert "mac_repeat" in session.stages
    assert "phone_camera_escalate" in session.stages
    assert "ack_cancelled" in session.stages
