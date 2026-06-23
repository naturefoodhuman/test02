# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:35:00

"""Unit tests for SessionDetector (E7-C4-S1-T1)."""

from pathlib import Path

from _infra.network.browser.session_detector import SessionDetector


def test_detect_login_required_chinese():
    result = SessionDetector().detect("请登录后继续访问")

    assert result.expired is True
    assert result.needs_login is True
    assert "登录" in result.matched_keywords
    assert result.reason == "login_required"


def test_detect_captcha_and_two_factor():
    text = "Sign in required. CAPTCHA shown. Enter 2FA verification code."
    result = SessionDetector().detect(text)

    assert result.expired is True
    assert result.needs_login is True
    assert result.needs_captcha is True
    assert result.needs_2fa is True
    assert result.needs_verification is True


def test_clean_snapshot_is_valid():
    result = SessionDetector().detect("Repository README and public content")

    assert result.expired is False
    assert result.reason == "session_valid"
    assert result.matched_keywords == []


def test_detect_from_snapshot_mapping():
    snapshot = {"title": "GitHub", "aria_snapshot": "Verify your identity to continue"}
    result = SessionDetector().detect(snapshot)

    assert result.expired is True
    assert result.needs_verification is True


def test_load_config_from_yaml(tmp_path):
    cfg = tmp_path / "session_keywords.yaml"
    cfg.write_text("login_page_patterns: ['LOGIN_ONLY']\ncaptcha_patterns: []\ntwo_factor_patterns: []\nverification_patterns: []\n", encoding="utf-8")

    detector = SessionDetector(SessionDetector.load_config(cfg))

    assert detector.detect("LOGIN_ONLY").needs_login is True
    assert detector.detect("Sign in").expired is False


def test_notify_uses_injected_notifier():
    calls = []
    detector = SessionDetector(notifier=lambda result: calls.append(result.reason))

    result = detector.detect("CAPTCHA", notify=True)

    assert result.expired is True
    assert calls == ["captcha_required"]
