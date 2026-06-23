# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 22:05:00

"""Security tests for PII bypass detection/redaction (E11-C4-S1-T1)."""

import asyncio
import re

import pytest

from _infra.network.privacy_gateway.canary import CanaryTokenMonitor
from _infra.network.privacy_gateway.gateway import PrivacyGateway


def run(coro):
    return asyncio.run(coro)


def build_test_gateway() -> PrivacyGateway:
    # No optional external detectors: this validates deterministic local layers.
    return PrivacyGateway(
        detectors=[],
        ner_detector=None,
        qwen_classifier=None,
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )


def assert_redacts(payload: str, expected_type: str = "CN_PHONE"):
    gateway = build_test_gateway()
    result = run(gateway.process_text(payload, source_url="security://pii-bypass"))

    assert any(entity["type"] == expected_type for entity in result.detections), result
    assert expected_type in result.text
    assert "13855551234" not in re.sub(r"\D", "", result.text)
    return result


@pytest.mark.parametrize(
    "payload",
    [
        "手机号：１３８５５５５１２３４",  # Unicode full-width homoglyphs
        "手机号：138\u200B5555\u200C1234",  # zero-width inserted
        "手机号：138%2D5555%2D1234",  # URL encoded separators
        "手机号：138-5555-1234",  # separator insertion
        "手机号：1 | 3 | 8 | 5 | 5 | 5 | 5 | 1 | 2 | 3 | 4",  # table-like split
        '{"contact": {"phone": "13855551234"}}',  # JSON key/value
        "phone_number = '13855551234'",  # code variable hiding
    ],
)
def test_cn_phone_bypass_payloads_are_redacted(payload):
    result = assert_redacts(payload, expected_type="CN_PHONE")
    assert "PII_CN_PHONE" in result.text


def test_base64_encoded_cn_phone_is_redacted():
    # base64('13855551234') == MTM4NTU1NTEyMzQ=
    payload = "encoded phone: MTM4NTU1NTEyMzQ="
    result = assert_redacts(payload, expected_type="CN_PHONE")

    assert "MTM4NTU1NTEyMzQ" not in result.text
    assert result.detections[0]["recognizer"].startswith("regex:base64")


def test_email_and_phone_in_json_are_both_redacted():
    payload = '{"email": "alice@example.com", "phone": "13855551234"}'
    gateway = build_test_gateway()

    result = run(gateway.process_text(payload))
    detected_types = {entity["type"] for entity in result.detections}

    assert "EMAIL_ADDRESS" in detected_types
    assert "CN_PHONE" in detected_types
    assert "alice@example.com" not in result.text
    assert "13855551234" not in result.text


def test_luhn_bank_card_with_spaces_is_redacted():
    payload = "bank card: 4111 1111 1111 1111"
    gateway = build_test_gateway()

    result = run(gateway.process_text(payload))

    assert any(entity["type"] == "BANK_CARD" for entity in result.detections)
    assert "4111 1111" not in result.text


def test_output_schema_still_forbids_raw_values_after_bypass_redaction():
    payload = "手机号：１３８５５５５１２３４"
    result = assert_redacts(payload, expected_type="CN_PHONE")

    output = result.to_output_dict()
    assert "value" not in output["entities"][0]
    assert "１３８" not in str(output)
    assert "13855551234" not in str(output)
