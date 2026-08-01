# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 03:05:00

"""Android native skeleton static tests."""

from __future__ import annotations

from pathlib import Path

ANDROID = Path("android/android")


def test_android_gradle_project_skeleton_exists() -> None:
    assert (ANDROID / "settings.gradle").exists()
    assert (ANDROID / "build.gradle").exists()
    assert (ANDROID / "app/build.gradle").exists()
    assert "com.android.application" in (ANDROID / "app/build.gradle").read_text()
    assert "applicationId 'com.aiparentingcopilot'" in (ANDROID / "app/build.gradle").read_text()


def test_android_manifest_has_alert_permissions_and_no_ios() -> None:
    manifest = (ANDROID / "app/src/main/AndroidManifest.xml").read_text()

    assert "android.permission.INTERNET" in manifest
    assert "android.permission.POST_NOTIFICATIONS" in manifest
    assert "android.permission.USE_FULL_SCREEN_INTENT" in manifest
    assert "android.permission.VIBRATE" in manifest
    assert "showWhenLocked" in manifest
    assert not Path("android/ios").exists()


def test_android_native_placeholders_and_e2e_exist() -> None:
    assert Path("android/src/native_modules/README.md").exists()
    assert Path("android/e2e/mvp_feeding.e2e.ts").exists()
    assert Path("android/e2e/red_alert_ack.e2e.ts").exists()


def test_android_native_fullscreen_alert_files_exist_and_are_trigger_only() -> None:
    base = ANDROID / "app/src/main/java/com/aiparentingcopilot"
    payload = (base / "AlertPayload.kt").read_text()
    activity = (base / "CriticalAlertActivity.kt").read_text()
    helper = (base / "NotificationHelper.kt").read_text()
    receiver = (base / "AlertActionReceiver.kt").read_text()
    manifest = (ANDROID / "app/src/main/AndroidManifest.xml").read_text()
    bridge = Path("android/src/notification/native_bridge.ts").read_text()

    assert "alert_id" in payload and "level" in payload and "type" in payload
    assert "evidence" not in payload and "recommended_action" not in payload
    assert "setShowWhenLocked(true)" in activity
    assert "setTurnScreenOn(true)" in activity
    assert "fullScreenIntent" in helper
    assert "IMPORTANCE_HIGH" in helper
    assert "recordLocalAction" in receiver
    assert ".CriticalAlertActivity" in manifest
    assert ".AlertActionReceiver" in manifest
    assert "shouldUseFullScreen" in bridge
