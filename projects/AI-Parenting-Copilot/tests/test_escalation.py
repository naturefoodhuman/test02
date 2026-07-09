# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""APC-T034 escalation state machine tests."""

from __future__ import annotations

import pytest

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.channels.fake import (
    FakeAppFullscreenChannel,
    FakeCameraSpeakerChannel,
    FakeFCMChannel,
    FakeMacSpeakerChannel,
)
from server.app.notification.escalation import EscalationPolicy, EscalationStateMachine
from server.app.notification.orchestrator import NotificationOrchestrator


def _machine() -> tuple[EscalationStateMachine, list[object]]:
    channels = [
        FakeFCMChannel(),
        FakeMacSpeakerChannel(),
        FakeAppFullscreenChannel(),
        FakeCameraSpeakerChannel(),
    ]
    return (
        EscalationStateMachine(
            NotificationOrchestrator(channels),
            policy=EscalationPolicy(repeat_seconds=60, escalate_seconds=90),
        ),
        channels,
    )


@pytest.mark.asyncio
async def test_red_alert_escalates_at_60_and_90_seconds() -> None:
    machine, _channels = _machine()
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")

    session = await machine.start(alert)
    await machine.advance(session, 60)
    await machine.advance(session, 30)

    assert session.stages == ["initial_fanout", "mac_repeat", "phone_camera_escalate"]
    assert len(session.receipts) >= 7


@pytest.mark.asyncio
async def test_ack_cancels_future_escalation_and_channels() -> None:
    machine, channels = _machine()
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")

    session = await machine.start(alert)
    await machine.ack(session, ack_by="u1", device_id="d1")
    await machine.advance(session, 120)

    assert session.acknowledged is True
    assert "mac_repeat" not in session.stages
    assert all(alert.id in channel.cancelled for channel in channels)  # type: ignore[attr-defined]
