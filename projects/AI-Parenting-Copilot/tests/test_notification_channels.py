# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 05:55:00

"""APC-T032 notification channel tests."""

from __future__ import annotations

import pytest

from server.app.notification.alert_repo import AlertLevel, AlertRecord
from server.app.notification.channels.fake import FakeFCMChannel


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


@pytest.mark.asyncio
async def test_channel_failure_returns_failed_receipt() -> None:
    alert = AlertRecord(baby_id="baby-1", family_id="family-1", level="yellow", type="feeding")
    receipt = await FakeFCMChannel(fail=True).send(alert)

    assert receipt.status == "failed"
    assert receipt.channel == "fcm"
