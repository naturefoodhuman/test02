# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 19:10:00

"""Android native skeleton static tests."""

from __future__ import annotations

from pathlib import Path

ANDROID = Path("android/android")


def test_android_gradle_project_skeleton_exists() -> None:
    assert (ANDROID / "settings.gradle").exists()
    assert (ANDROID / "build.gradle").exists()
    assert (ANDROID / "app/build.gradle").exists()
    assert (ANDROID / "gradlew").exists()
    assert (ANDROID / "gradlew").stat().st_mode & 0o111
    assert (ANDROID / "gradle/wrapper/gradle-wrapper.properties").exists()
    assert "com.android.application" in (ANDROID / "app/build.gradle").read_text()
    assert "applicationId 'com.aiparentingcopilot'" in (ANDROID / "app/build.gradle").read_text()
    wrapper = (ANDROID / "gradle/wrapper/gradle-wrapper.properties").read_text()
    assert "gradle-8.10.2-bin.zip" in wrapper


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


def test_android_native_local_event_store_supports_pending_sync_contract() -> None:
    base = ANDROID / "app/src/main/java/com/aiparentingcopilot"
    event = (base / "LocalObservationEvent.kt").read_text()
    store = (base / "LocalEventStore.kt").read_text()
    bridge = Path("android/src/sync/native_sqlite_bridge.ts").read_text()

    assert "pendingSync" in event
    assert "SQLiteOpenHelper" in store
    assert "observation_event_local" in store
    assert "insertPending" in store
    assert "markSynced" in store
    assert "pending_sync" in store
    manifest = (ANDROID / "app/src/main/AndroidManifest.xml").read_text()
    main = (base / "MainActivity.kt").read_text()
    quick = (base / "QuickRecordActivity.kt").read_text()
    pending = (base / "PendingEventsActivity.kt").read_text()

    native_api = (base / "NativeApiClient.kt").read_text()
    pending_drainer = (base / "PendingSyncDrainer.kt").read_text()
    alert_drainer = (base / "AlertAckDrainer.kt").read_text()
    alert_receiver = (base / "AlertActionReceiver.kt").read_text()

    assert "NativeLocalEventBridge" in bridge
    assert "pendingSyncCount" in bridge
    assert "QuickRecordActivity" in manifest
    assert "PendingEventsActivity" in manifest
    assert "QuickRecordActivity::class.java" in main
    assert "LocalEventStore" in quick and "insertPending" in quick
    assert "Pending sync:" in quick
    background = (base / "BackgroundDrainJobService.kt").read_text()
    scheduler = (base / "BackgroundDrainScheduler.kt").read_text()
    settings = (base / "ApiSettingsStore.kt").read_text()
    settings_activity = (base / "ApiSettingsActivity.kt").read_text()
    boot = (base / "BootReceiver.kt").read_text()

    assert "Pending sync events" in pending
    assert "PendingSyncDrainer" in pending
    assert "postJson" in native_api
    assert "/api/v1/events" in pending_drainer
    assert "markSynced" in pending_drainer
    assert "/api/v1/alerts/" in alert_drainer
    assert "drainLocalActions" in alert_receiver
    assert "JobService" in background
    assert "JobScheduler" in scheduler
    assert "schedulePeriodic" in scheduler
    assert "api_base_url" in settings
    assert "Trigger drain now" in settings_activity
    assert "BOOT_COMPLETED" in boot
    assert "BackgroundDrainJobService" in manifest
    assert "BootReceiver" in manifest
    today = (base / "TodayActivity.kt").read_text()
    timeline = (base / "TimelineActivity.kt").read_text()
    alert_center = (base / "AlertCenterActivity.kt").read_text()
    sleep = (base / "SleepSessionActivity.kt").read_text()

    assert "ApiSettingsActivity::class.java" in main
    assert "TodayActivity::class.java" in main
    assert "TimelineActivity::class.java" in main
    assert "AlertCenterActivity::class.java" in main
    assert "SleepSessionActivity::class.java" in main
    assert "Refresh server health" in today
    assert "/api/v1/system/health" in today
    assert "Refresh server timeline" in timeline
    assert "/api/v1/events?baby_id=" in timeline
    assert "Refresh server alerts" in alert_center
    assert "Submit useful feedback" in alert_center
    assert "AlertAckDrainer" in alert_center
    assert "/api/v1/alerts?family_id=" in alert_center
    assert "/feedback" in alert_center
    assert "/api/v1/sleep-sessions" in sleep
    assert "putJsonResult" in sleep
    assert "/roi" in sleep
    assert "/camera-events" in sleep
    assert "postSessionAction" in sleep
    assert ".TodayActivity" in manifest
    assert ".AlertCenterActivity" in manifest


def test_android_native_secure_session_store_uses_keystore() -> None:
    base = ANDROID / "app/src/main/java/com/aiparentingcopilot"
    secure = (base / "SecureSessionStore.kt").read_text()
    bridge = Path("android/src/features/auth/native_secure_session.ts").read_text()

    assert "AndroidKeyStore" in secure
    assert "AES/GCM/NoPadding" in secure
    assert "accessToken" in secure
    assert "clear()" in secure
    assert "NativeSecureSessionBridge" in bridge
    assert "persistSession" in bridge
    assert "restoreSession" in bridge
