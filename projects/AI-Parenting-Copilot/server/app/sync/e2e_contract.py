# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:48:00

"""Android/PowerSync MVP E2E contract report.

This report is a deterministic substitute for real-device execution. It verifies
that Android offline-first files still expose the required local event schema,
pending drain routes, heartbeat route, and Today pending visibility while server-side
sync contract validation accepts the same shape.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from server.app.sync.service.contract_validator import validate_sync_record

REQUIRED_ANDROID_FILES = (
    "android/src/sync/schema.ts",
    "android/src/sync/pending_sync_drain.ts",
    "android/src/sync/native_sqlite_bridge.ts",
    "android/src/features/auth/authService.ts",
    "android/src/features/auth/native_secure_session.ts",
    "android/src/features/quick_record/createLocalEvent.ts",
    "android/src/features/quick_record/copilotFlow.ts",
    "android/src/features/today/viewModel.ts",
    "android/src/features/timeline/viewModel.ts",
    "android/src/features/alert_center/viewModel.ts",
    "android/src/features/sleep_session/viewModel.ts",
    "android/android/app/src/main/java/com/aiparentingcopilot/LoginActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/SecureSessionStore.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/MainActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/PendingSyncDrainer.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/TodayActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/TimelineActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/AlertCenterActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/SleepSessionActivity.kt",
)

REQUIRED_COLUMNS = (
    "event_id",
    "baby_id",
    "family_id",
    "user_id",
    "device_id",
    "event_type",
    "client_created_at",
    "start_time",
    "payload",
    "source",
    "confidence",
    "pending_sync",
)


@dataclass(frozen=True, slots=True)
class AndroidE2EContractReport:
    ok: bool
    checks: dict[str, str]
    errors: tuple[str, ...]
    sample_event: dict[str, Any]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_android_e2e_contract_report(project_root: Path | str = ".") -> AndroidE2EContractReport:
    root = Path(project_root)
    checks: dict[str, str] = {}
    errors: list[str] = []
    for rel in REQUIRED_ANDROID_FILES:
        _expect((root / rel).exists(), f"file:{rel}", checks, errors)
    schema_text = _read(root / "android/src/sync/schema.ts")
    for column in REQUIRED_COLUMNS:
        _expect(f"'{column}'" in schema_text, f"schema_column:{column}", checks, errors)
    auth_service = _read(root / "android/src/features/auth/authService.ts")
    _expect("/api/v1/auth/login" in auth_service, "ts_auth_login_route", checks, errors)
    _expect(
        "/api/v1/auth/devices/register" in auth_service,
        "ts_auth_device_register_route",
        checks,
        errors,
    )
    secure_session_ts = _read(root / "android/src/features/auth/native_secure_session.ts")
    _expect(
        "NativeSecureSessionBridge" in secure_session_ts,
        "ts_secure_session_bridge",
        checks,
        errors,
    )
    pending_drain = _read(root / "android/src/sync/pending_sync_drain.ts")
    _expect("/api/v1/events" in pending_drain, "ts_drain_events_route", checks, errors)
    _expect("/api/v1/sync/heartbeat" in pending_drain, "ts_drain_heartbeat_route", checks, errors)
    main_activity = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/MainActivity.kt"
    )
    _expect("LoginActivity::class.java" in main_activity, "native_main_login_entry", checks, errors)
    _expect("TodayActivity::class.java" in main_activity, "native_main_today_entry", checks, errors)
    _expect(
        "QuickRecordActivity::class.java" in main_activity,
        "native_main_quick_record_entry",
        checks,
        errors,
    )
    _expect(
        "TimelineActivity::class.java" in main_activity,
        "native_main_timeline_entry",
        checks,
        errors,
    )
    _expect(
        "AlertCenterActivity::class.java" in main_activity,
        "native_main_alert_center_entry",
        checks,
        errors,
    )
    _expect(
        "SleepSessionActivity::class.java" in main_activity,
        "native_main_sleep_session_entry",
        checks,
        errors,
    )
    login_activity = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/LoginActivity.kt"
    )
    _expect("/api/v1/auth/login" in login_activity, "native_login_route", checks, errors)
    _expect(
        "/api/v1/auth/devices/register" in login_activity,
        "native_device_register_route",
        checks,
        errors,
    )
    _expect("SecureSessionStore" in login_activity, "native_login_secure_store", checks, errors)
    secure_session = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/SecureSessionStore.kt"
    )
    _expect("AndroidKeyStore" in secure_session, "native_keystore", checks, errors)
    _expect("AES/GCM/NoPadding" in secure_session, "native_session_aes_gcm", checks, errors)
    quick_record = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt"
    )
    _expect("insertPending" in quick_record, "native_quick_record_insert_pending", checks, errors)
    _expect(
        "saveFallbackCandidate" in quick_record,
        "native_quick_record_offline_fallback",
        checks,
        errors,
    )
    pending_native = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/PendingSyncDrainer.kt"
    )
    _expect("/api/v1/events" in pending_native, "native_drain_events_route", checks, errors)
    _expect(
        "/api/v1/sync/heartbeat" in pending_native,
        "native_drain_heartbeat_route",
        checks,
        errors,
    )
    today = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/TodayActivity.kt"
    )
    _expect("Pending sync:" in today, "today_pending_visible", checks, errors)
    _expect("/api/v1/system/health" in today, "native_today_health_route", checks, errors)
    today_view_model = _read(root / "android/src/features/today/viewModel.ts")
    _expect("pendingSyncCount" in today_view_model, "ts_today_pending_sync_count", checks, errors)
    _expect("grayDeviceCount" in today_view_model, "ts_today_gray_device_count", checks, errors)
    _expect("/api/v1/system/health" in today_view_model, "ts_today_health_route", checks, errors)
    _expect(
        "/api/v1/babies/${babyId}/state" in today_view_model,
        "ts_today_state_route",
        checks,
        errors,
    )

    timeline_native = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/TimelineActivity.kt"
    )
    _expect(
        "/api/v1/events?baby_id=" in timeline_native,
        "native_timeline_events_route",
        checks,
        errors,
    )
    timeline_vm = _read(root / "android/src/features/timeline/viewModel.ts")
    _expect(
        "/api/v1/events?baby_id=${babyId}" in timeline_vm,
        "ts_timeline_events_route",
        checks,
        errors,
    )
    _expect("/correct" in timeline_vm, "ts_timeline_correction_route", checks, errors)
    _expect(
        "delete<LocalObservationEvent>" in timeline_vm,
        "ts_timeline_soft_delete",
        checks,
        errors,
    )
    _expect("5 * 60 * 1000" in timeline_vm, "ts_timeline_duplicate_hint", checks, errors)

    alert_native = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/AlertCenterActivity.kt"
    )
    _expect(
        "/api/v1/alerts?family_id=" in alert_native,
        "native_alert_list_route",
        checks,
        errors,
    )
    _expect("/feedback" in alert_native, "native_alert_feedback_route", checks, errors)
    _expect("AlertAckDrainer" in alert_native, "native_alert_ack_drainer", checks, errors)
    alert_vm = _read(root / "android/src/features/alert_center/viewModel.ts")
    _expect(
        "/api/v1/alerts?family_id=${familyId}" in alert_vm,
        "ts_alert_list_route",
        checks,
        errors,
    )
    _expect("/deliveries" in alert_vm, "ts_alert_deliveries_route", checks, errors)
    _expect("/dispatch" in alert_vm, "ts_alert_dispatch_route", checks, errors)
    _expect("/ack" in alert_vm, "ts_alert_ack_route", checks, errors)
    _expect("/feedback" in alert_vm, "ts_alert_feedback_route", checks, errors)

    sleep_native = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/SleepSessionActivity.kt"
    )
    _expect(
        "/api/v1/sleep-sessions" in sleep_native,
        "native_sleep_start_route",
        checks,
        errors,
    )
    _expect("/roi" in sleep_native, "native_sleep_roi_route", checks, errors)
    _expect(
        "/camera-events" in sleep_native,
        "native_sleep_camera_events_route",
        checks,
        errors,
    )
    sleep_vm = _read(root / "android/src/features/sleep_session/viewModel.ts")
    _expect("/api/v1/sleep-sessions" in sleep_vm, "ts_sleep_start_route", checks, errors)
    _expect("/pause" in sleep_vm, "ts_sleep_pause_route", checks, errors)
    _expect("/resume" in sleep_vm, "ts_sleep_resume_route", checks, errors)
    _expect("/end" in sleep_vm, "ts_sleep_end_route", checks, errors)
    _expect("/roi" in sleep_vm, "ts_sleep_roi_route", checks, errors)
    _expect("/camera-events" in sleep_vm, "ts_sleep_camera_events_route", checks, errors)
    _expect("/shadow-summary" in sleep_vm, "ts_sleep_shadow_summary_route", checks, errors)
    _expect(
        "/api/v1/camera-shadow/evaluate" in sleep_vm,
        "ts_sleep_shadow_evaluate_route",
        checks,
        errors,
    )
    _expect("影子模式，不强提醒" in sleep_vm, "ts_sleep_shadow_label", checks, errors)

    sample_event = _sample_sync_event()
    try:
        validate_sync_record(sample_event)
        checks["server_sync_contract_sample"] = "ok"
    except Exception as exc:
        checks["server_sync_contract_sample"] = "failed"
        errors.append(f"sample event rejected by server sync contract: {exc}")
    return AndroidE2EContractReport(
        ok=not errors,
        checks=checks,
        errors=tuple(errors),
        sample_event=sample_event,
    )


def _sample_sync_event() -> dict[str, Any]:
    now = datetime(2026, 8, 4, tzinfo=UTC).isoformat()
    return {
        "event_id": "android-e2e-sample-event",
        "baby_id": "baby-e2e",
        "family_id": "family-e2e",
        "user_id": "user-e2e",
        "device_id": "device-e2e",
        "event_type": "feeding",
        "client_created_at": now,
        "start_time": now,
        "payload": {"amount_ml": 90},
        "source": "manual",
        "confidence": 1.0,
        "is_deleted": False,
        "correction_of": None,
    }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _expect(
    condition: bool,
    check_name: str,
    checks: dict[str, str],
    errors: list[str],
) -> None:
    checks[check_name] = "ok" if condition else "failed"
    if not condition:
        errors.append(f"Android E2E contract failed: {check_name}")
