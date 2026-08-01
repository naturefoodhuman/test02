# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 01:05:00

"""APC-T032 notification channel tests."""

from __future__ import annotations

import pytest

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.channel_factory import build_default_channels
from server.app.notification.channels.fake import FakeFCMChannel
from server.app.notification.channels.fcm import FCMChannel, build_fcm_trigger_payload
from server.app.notification.channels.mac_speaker import MacSpeakerChannel, safe_spoken_alert


@pytest.mark.asyncio
async def test_fcm_payload_contains_only_alert_trigger_fields() -> None:
    alert = AlertRecord(
        baby_id="baby-1",
        family_id="family-1",
        level=AlertLevel.RED,
        type="triage",
        evidence={"private": "do-not-send"},
        recommended_action="private action",
    )
    channel = FakeFCMChannel()
    receipt = await channel.send(alert)

    payload = receipt.receipt["payload"]
    assert payload == {"alert_id": alert.id, "level": "red", "type": "triage"}
    assert "private" not in str(payload)
    assert receipt.status == "sent"


def test_real_fcm_adapter_payload_is_trigger_only() -> None:
    alert = AlertRecord(
        baby_id="baby-1",
        family_id="family-1",
        level=AlertLevel.RED,
        type="triage",
        evidence={"private": "do-not-send"},
        recommended_action="private action",
    )

    payload = build_fcm_trigger_payload(alert)

    assert payload == {"alert_id": alert.id, "level": "red", "type": "triage"}
    assert "private" not in str(payload)


@pytest.mark.asyncio
async def test_default_channels_are_safe_dry_run_adapters() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level=AlertLevel.RED, type="triage")
    channels = build_default_channels(include_camera=True)

    receipts = [await channel.send(alert) for channel in channels]

    assert {receipt.channel for receipt in receipts} == {
        "fcm",
        "mac_speaker",
        "app_fullscreen",
        "camera_speaker",
    }
    assert {receipt.status for receipt in receipts}.issubset({"dry_run", "queued"})
    assert safe_spoken_alert(alert).startswith("育儿副驾驶提醒")
    assert isinstance(channels[0], FCMChannel)
    assert isinstance(channels[1], MacSpeakerChannel)


@pytest.mark.asyncio
async def test_channel_failure_returns_failed_receipt() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level="yellow", type="feeding")
    receipt = await FakeFCMChannel(fail=True).send(alert)

    assert receipt.status == "failed"
    assert receipt.channel == "fcm"
