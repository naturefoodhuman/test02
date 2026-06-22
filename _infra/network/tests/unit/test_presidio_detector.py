# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:41:55

"""
Unit tests for PresidioDetector (E5-C3-S1-T2).

Uses asyncio.run() to match project convention (no pytest-asyncio).
These tests require the optional ``presidio_analyzer`` dependency; they are
skipped in minimal sandbox environments where that dependency is not installed.
"""

import asyncio

import pytest

pytest.importorskip("presidio_analyzer")

from _infra.network.privacy_gateway.detectors.presidio_detector import PresidioDetector
from _infra.network.privacy_gateway.models import PIIType


def detector():
    # Use a function instead of fixture for simplicity with asyncio.run
    return PresidioDetector(language="en", timeout=8.0)


def test_presidio_detector_instantiation():
    det = PresidioDetector()
    assert det.get_name() == "presidio"


def test_presidio_detect_email():
    det = detector()
    text = "Please contact me at alice@example.com for details."
    entities = asyncio.run(det.detect(text))

    emails = [e for e in entities if e.type == PIIType.EMAIL_ADDRESS]
    assert len(emails) >= 1
    assert any("alice@example.com" in e.value for e in emails)
    assert emails[0].recognizer.startswith("presidio:")


def test_presidio_detect_credit_card():
    det = detector()
    text = "My card number is 4111-1111-1111-1111 thanks."
    entities = asyncio.run(det.detect(text))

    cards = [e for e in entities if e.type == PIIType.CREDIT_CARD]
    assert len(cards) >= 1
    assert "4111" in cards[0].value


def test_presidio_detect_multiple():
    det = detector()
    text = "Email: bob@test.org and phone +1-202-555-0123"
    entities = asyncio.run(det.detect(text))

    types = {e.type for e in entities}
    assert PIIType.EMAIL_ADDRESS in types


def test_presidio_health_check():
    det = detector()
    healthy = asyncio.run(det.health_check())
    assert healthy is True


def test_presidio_supports_type():
    det = detector()
    assert det.supports_type(PIIType.EMAIL_ADDRESS) is True
    assert det.supports_type(PIIType.CREDIT_CARD) is True
    assert det.supports_type(PIIType.API_KEY) is True
    assert det.supports_type(PIIType.JWT) is True
    assert det.supports_type(PIIType.COOKIE) is True
