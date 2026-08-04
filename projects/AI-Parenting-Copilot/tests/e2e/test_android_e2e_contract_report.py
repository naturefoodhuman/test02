# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:48:00

"""Android/PowerSync MVP E2E contract report tests."""

from __future__ import annotations

from pathlib import Path

from server.app.sync.e2e_contract import build_android_e2e_contract_report


def test_android_e2e_contract_report_passes_static_and_server_contracts() -> None:
    report = build_android_e2e_contract_report(Path("."))

    assert report.ok is True
    assert report.checks["ts_auth_login_route"] == "ok"
    assert report.checks["native_login_route"] == "ok"
    assert report.checks["native_device_register_route"] == "ok"
    assert report.checks["native_keystore"] == "ok"
    assert report.checks["native_quick_record_insert_pending"] == "ok"
    assert report.checks["native_quick_record_offline_fallback"] == "ok"
    assert report.checks["native_drain_heartbeat_route"] == "ok"
    assert report.checks["today_pending_visible"] == "ok"
    assert report.checks["ts_today_state_route"] == "ok"
    assert report.checks["native_timeline_events_route"] == "ok"
    assert report.checks["ts_timeline_correction_route"] == "ok"
    assert report.checks["ts_timeline_soft_delete"] == "ok"
    assert report.checks["native_alert_list_route"] == "ok"
    assert report.checks["native_alert_ack_drainer"] == "ok"
    assert report.checks["ts_alert_ack_route"] == "ok"
    assert report.checks["ts_alert_feedback_route"] == "ok"
    assert report.checks["native_sleep_start_route"] == "ok"
    assert report.checks["ts_sleep_roi_route"] == "ok"
    assert report.checks["ts_sleep_shadow_evaluate_route"] == "ok"
    assert report.checks["server_sync_contract_sample"] == "ok"
    assert report.sample_event["event_type"] == "feeding"
