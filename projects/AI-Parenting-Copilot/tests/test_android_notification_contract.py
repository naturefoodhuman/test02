# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:20:00

"""Android notification contract report tests for APC-T052."""

from __future__ import annotations

from pathlib import Path

from server.app.notification.android_contract import build_android_notification_contract_report


def test_android_notification_contract_report_passes() -> None:
    report = build_android_notification_contract_report(Path("."))

    assert report.ok is True
    assert report.checks["manifest_permission:android.permission.USE_FULL_SCREEN_INTENT"] == "ok"
    assert report.checks["native_high_importance_channel"] == "ok"
    assert report.checks["native_fullscreen_intent"] == "ok"
    assert report.checks["trigger_payload_no_evidence"] == "ok"
    assert report.checks["native_ack_retry_exception_safe"] == "ok"
    assert report.checks["ts_fcm_no_evidence"] == "ok"
    assert report.checks["ts_fetch_alert_detail"] == "ok"
