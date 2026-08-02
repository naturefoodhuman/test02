# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-02 05:22:00

"""APC-T049/T050/T051/T052/T053 Android feature static tests."""

from __future__ import annotations

from pathlib import Path

ANDROID = Path("android/src")


def test_quick_record_copilot_flow_uses_server_candidate_with_local_fallback() -> None:
    source = (ANDROID / "features/quick_record/copilotFlow.ts").read_text()
    native = (
        Path("android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt")
        .read_text()
    )

    assert "fetchCopilotRecordCandidate" in source
    assert "mapServerRecordCandidate" in source
    assert "confirmCopilotRecordCandidate" in source
    assert "createLocalEventFromCopilotText" in source
    assert "/api/v1/copilot/query" in source
    assert "/api/v1/copilot/record-candidates/confirm" in source
    assert "buildRecordCandidate(text)" in source
    assert "Parse text with Copilot and save locally" in native
    assert "/api/v1/copilot/query" in native
    assert "saveFallbackCandidate" in native
    assert "Copilot error" in native
    assert "insertPending" in native


def test_today_view_model_displays_pending_sync_and_gray_devices() -> None:
    source = (ANDROID / "features/today/viewModel.ts").read_text()

    assert "pendingSyncCount" in source
    assert "grayDeviceCount" in source
    assert "lastFeedingText" in source
    assert "DeviceHealthSnapshot" in source
    assert "fetchTodayServerSnapshot" in source
    assert "/api/v1/system/health" in source
    assert "/api/v1/babies/${babyId}/state" in source


def test_timeline_view_model_supports_correction_soft_delete_and_duplicate_hint() -> None:
    source = (ANDROID / "features/timeline/viewModel.ts").read_text()

    assert "createCorrectionPayload" in source
    assert "createSoftDeletePayload" in source
    assert "duplicateFeedingHint" in source
    assert "5 * 60 * 1000" in source
    assert "fetchTimeline" in source
    assert "submitCorrection" in source
    assert "softDeleteEvent" in source
    assert "/api/v1/events?baby_id=${babyId}" in source


def test_alert_center_fetches_detail_and_supports_ack_feedback() -> None:
    source = (ANDROID / "features/alert_center/viewModel.ts").read_text()

    assert "FeedbackType" in source
    assert "ackAlert" in source
    assert "submitFeedback" in source
    assert "fetchAlerts" in source
    assert "fetchAlertDeliveries" in source
    assert "dispatchAlert" in source
    assert "/api/v1/alerts/${alertId}/ack" in source
    assert "/api/v1/alerts/${alertId}/deliveries" in source


def test_android_notification_payload_is_trigger_only_and_high_priority_for_red_or_orange() -> None:
    fcm = (ANDROID / "notification/fcm.ts").read_text()
    channels = (ANDROID / "notification/notifee_channels.ts").read_text()
    fullscreen = (ANDROID / "notification/fullscreen_intent.ts").read_text()
    fallback = (ANDROID / "notification/fallback.ts").read_text()
    ack_drain = (ANDROID / "notification/ack_drain.ts").read_text()
    work = (ANDROID / "background/work_manager.ts").read_text()

    assert "alert_id" in fcm and "level" in fcm and "type" in fcm
    assert "evidence" not in fcm
    assert "importance: high ? 'high'" in channels
    assert "USE_FULL_SCREEN_INTENT" in fullscreen
    assert "startLocalFallback" in fallback and "stopLocalFallback" in fallback
    assert "drainLocalAlertActions" in ack_drain
    assert "/api/v1/alerts/${action.alert_id}/ack" in ack_drain
    assert "pending_sync" in work


def test_sleep_session_view_model_active_gate_and_roi_save() -> None:
    source = (ANDROID / "features/sleep_session/viewModel.ts").read_text()

    assert "analysisVisible: session?.state === 'active'" in source
    assert "影子模式，不强提醒" in source
    assert "saveROI" in source
    assert "startSleepSession" in source
    assert "pauseSleepSession" in source
    assert "resumeSleepSession" in source
    assert "endSleepSession" in source
    assert "fetchCameraEvents" in source
    assert "fetchCameraShadowSummary" in source
    assert "evaluateCameraShadow" in source
    assert "/api/v1/sleep-sessions/${sessionId}/roi" in source
    assert "/api/v1/sleep-sessions/${sessionId}/camera-events" in source
    assert "/api/v1/sleep-sessions/${sessionId}/shadow-summary" in source
    assert "/api/v1/camera-shadow/evaluate" in source
