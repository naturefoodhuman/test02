# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 20:10:00

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
