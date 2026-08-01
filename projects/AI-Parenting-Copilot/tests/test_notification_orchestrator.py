# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 02:15:00

"""APC-T033 Notification Orchestrator tests."""

from __future__ import annotations

import pytest

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.channels.fake import (
    FakeAppFullscreenChannel,
    FakeCameraSpeakerChannel,
    FakeFCMChannel,
    FakeMacSpeakerChannel,
)
from server.app.notification.orchestrator import NotificationOrchestrator


@pytest.mark.asyncio
async def test_red_alert_fans_out_to_multiple_channels_and_records_receipts() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")
    orchestrator = NotificationOrchestrator(
        [
            FakeFCMChannel(),
            FakeMacSpeakerChannel(),
            FakeAppFullscreenChannel(),
            FakeCameraSpeakerChannel(),
        ]
    )

    receipts = await orchestrator.dispatch(alert)

    assert {receipt.channel for receipt in receipts} == {
        "fcm",
        "mac_speaker",
        "app_fullscreen",
        "camera_speaker",
    }
    assert len(await orchestrator.delivery_repo.list_by_alert(alert.id)) == 4


@pytest.mark.asyncio
async def test_fcm_failure_does_not_block_mac_or_app_fallback() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")
    orchestrator = NotificationOrchestrator(
        [FakeFCMChannel(fail=True), FakeMacSpeakerChannel(), FakeAppFullscreenChannel()]
    )

    receipts = await orchestrator.dispatch(alert)

    status_by_channel = {receipt.channel: receipt.status for receipt in receipts}
    assert status_by_channel["fcm"] == "failed"
    assert status_by_channel["mac_speaker"] == "sent"
    assert status_by_channel["app_fullscreen"] == "sent"


@pytest.mark.asyncio
async def test_cancel_records_channel_cancellation_receipts() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")
    channels = [FakeFCMChannel(), FakeMacSpeakerChannel(), FakeAppFullscreenChannel()]
    orchestrator = NotificationOrchestrator(channels)

    receipts = await orchestrator.cancel(alert)

    assert {receipt.channel for receipt in receipts} == {"fcm", "mac_speaker", "app_fullscreen"}
    assert {receipt.status for receipt in receipts} == {"cancelled"}
    assert len(await orchestrator.delivery_repo.list_by_alert(alert.id)) == 3
    assert all(alert.id in channel.cancelled for channel in channels)
