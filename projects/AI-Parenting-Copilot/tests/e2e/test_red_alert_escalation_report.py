# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:12:00

"""Red alert fake-channel escalation E2E substitute."""

from __future__ import annotations

import pytest

from server.app.notification.escalation_report import simulate_red_alert_escalation


@pytest.mark.asyncio
async def test_red_alert_escalation_report_uses_trigger_only_payloads_and_cancel() -> None:
    report = await simulate_red_alert_escalation()

    assert "initial_fanout" in report.stages
    assert "mac_repeat" in report.stages
    assert "phone_camera_escalate" in report.stages
    assert "ack_cancelled" in report.stages
    assert set(report.receipt_channels) >= {
        "fcm",
        "mac_speaker",
        "app_fullscreen",
        "camera_speaker",
    }
    assert report.trigger_only_payloads is True
    assert report.acknowledged is True
    assert set(report.cancelled_channels) == {
        "fcm",
        "mac_speaker",
        "app_fullscreen",
        "camera_speaker",
    }
