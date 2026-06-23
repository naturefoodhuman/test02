# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:05:00

"""Unit tests for BrowserActionClassifier (E7-C5-S1-T1)."""

from _infra.network.browser.action_classifier import BrowserAction, BrowserActionClassifier, BrowserActionRisk, classify_action


def test_read_only_action_classified():
    result = classify_action(BrowserAction(action_type="snapshot", target="main"))

    assert result.risk == BrowserActionRisk.READ_ONLY
    assert result.approval_required is False
    assert result.reason == "read_only_action"


def test_low_risk_navigation_classified():
    result = classify_action(BrowserAction(action_type="open", page_url="https://example.com"))

    assert result.risk == BrowserActionRisk.LOW_RISK
    assert result.approval_required is False


def test_high_risk_tool_name_requires_approval():
    result = classify_action(BrowserAction(action_type="delete", target="repo"))

    assert result.risk == BrowserActionRisk.HIGH_RISK
    assert result.approval_required is True
    assert "delete" in result.matched_terms


def test_high_risk_payload_hint_requires_approval():
    action = BrowserAction(action_type="click", target="button", payload={"label": "Confirm purchase"})

    result = BrowserActionClassifier().classify(action)

    assert result.risk == BrowserActionRisk.HIGH_RISK
    assert result.approval_required is True
    assert "purchase" in result.matched_terms or "confirm" in result.matched_terms
    assert result.diff_preview["target"] == "button"
    assert result.diff_preview["payload_keys"] == ["label"]


def test_send_email_action_requires_approval():
    result = classify_action(BrowserAction(action_type="send_email", payload={"to": "a@example.com"}))

    assert result.risk == BrowserActionRisk.HIGH_RISK
    assert result.approval_required is True
    assert "send_email" in result.matched_terms


def test_custom_high_risk_action():
    classifier = BrowserActionClassifier(high_risk_actions={"archive"}, high_risk_hints=set())

    result = classifier.classify(BrowserAction(action_type="archive"))

    assert result.risk == BrowserActionRisk.HIGH_RISK
    assert result.approval_required is True
