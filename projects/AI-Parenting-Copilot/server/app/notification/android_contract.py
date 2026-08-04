# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:20:00

"""Android notification/full-screen alert contract report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AndroidNotificationContractReport:
    ok: bool
    checks: dict[str, str]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_android_notification_contract_report(
    project_root: Path | str = ".",
) -> AndroidNotificationContractReport:
    root = Path(project_root)
    checks: dict[str, str] = {}
    errors: list[str] = []
    manifest = _read(root / "android/android/app/src/main/AndroidManifest.xml")
    helper = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/NotificationHelper.kt"
    )
    payload = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/AlertPayload.kt"
    )
    critical = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/CriticalAlertActivity.kt"
    )
    receiver = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/AlertActionReceiver.kt"
    )
    ack_drainer = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/AlertAckDrainer.kt"
    )
    fcm = _read(root / "android/src/notification/fcm.ts")
    fullscreen = _read(root / "android/src/notification/fullscreen_intent.ts")
    fallback = _read(root / "android/src/notification/fallback.ts")
    work = _read(root / "android/src/background/work_manager.ts")

    for permission in (
        "android.permission.POST_NOTIFICATIONS",
        "android.permission.USE_FULL_SCREEN_INTENT",
        "android.permission.VIBRATE",
        "android.permission.WAKE_LOCK",
    ):
        _expect(permission in manifest, f"manifest_permission:{permission}", checks, errors)
    _expect(".CriticalAlertActivity" in manifest, "manifest_critical_activity", checks, errors)
    _expect(".AlertActionReceiver" in manifest, "manifest_alert_receiver", checks, errors)
    _expect("showWhenLocked" in manifest, "manifest_show_when_locked", checks, errors)
    _expect("turnScreenOn" in manifest, "manifest_turn_screen_on", checks, errors)

    _expect("IMPORTANCE_HIGH" in helper, "native_high_importance_channel", checks, errors)
    _expect("fullScreenIntent" in helper, "native_fullscreen_intent", checks, errors)
    _expect(
        "alert_id" in payload and "level" in payload and "type" in payload,
        "trigger_fields",
        checks,
        errors,
    )
    _expect("evidence" not in payload, "trigger_payload_no_evidence", checks, errors)
    _expect(
        "recommended_action" not in payload,
        "trigger_payload_no_recommendation",
        checks,
        errors,
    )
    _expect("setShowWhenLocked(true)" in critical, "native_show_when_locked", checks, errors)
    _expect("setTurnScreenOn(true)" in critical, "native_turn_screen_on", checks, errors)
    _expect("Open the app for evidence" in critical, "native_detail_fetch_guidance", checks, errors)
    _expect("recordLocalAction" in receiver, "native_local_ack_record", checks, errors)
    _expect(
        "catch (_: Exception)" in ack_drainer,
        "native_ack_retry_exception_safe",
        checks,
        errors,
    )

    _expect(
        "alert_id" in fcm and "level" in fcm and "type" in fcm,
        "ts_fcm_trigger_fields",
        checks,
        errors,
    )
    _expect("evidence" not in fcm, "ts_fcm_no_evidence", checks, errors)
    _expect("/api/v1/alerts/${payload.alert_id}" in fcm, "ts_fetch_alert_detail", checks, errors)
    _expect(
        "USE_FULL_SCREEN_INTENT" in fullscreen,
        "ts_fullscreen_permission_guide",
        checks,
        errors,
    )
    _expect("startLocalFallback" in fallback, "ts_local_fallback_start", checks, errors)
    _expect("stopLocalFallback" in fallback, "ts_local_fallback_stop", checks, errors)
    _expect("pending_sync" in work, "ts_background_pending_sync_work", checks, errors)

    return AndroidNotificationContractReport(ok=not errors, checks=checks, errors=tuple(errors))


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
        errors.append(f"Android notification contract failed: {check_name}")
