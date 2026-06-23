# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 22:20:00

"""End-to-end style Canary Token tests (E11-C6-S1-T1)."""

import asyncio
import json

import pytest

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.exceptions import CanaryTokenDetectedError
from _infra.network.input_sanitizer.sanitizer import sanitize
from _infra.network.privacy_gateway.canary import CanaryTokenMonitor, DEFAULT_CANARY_TOKEN
from _infra.network.privacy_gateway.gateway import PrivacyContext, PrivacyGateway


def run(coro):
    return asyncio.run(coro)


def build_gateway(audit_logger=None) -> PrivacyGateway:
    return PrivacyGateway(
        detectors=[],
        ner_detector=None,
        qwen_classifier=None,
        canary_monitor=CanaryTokenMonitor(tokens=[DEFAULT_CANARY_TOKEN], audit_logger=audit_logger),
        enable_presidio_default=False,
        enable_ner_default=False,
    )


@pytest.mark.parametrize(
    ("location", "payload"),
    [
        (
            "search_result",
            f"Search title: public result. Snippet contains {DEFAULT_CANARY_TOKEN}_search.",
        ),
        (
            "extracted_markdown",
            f"# Extracted Page\n\nUseful facts.\n\n{DEFAULT_CANARY_TOKEN}_markdown",
        ),
        (
            "privacy_output",
            f"Final redacted markdown accidentally includes {DEFAULT_CANARY_TOKEN}_output",
        ),
    ],
)
def test_canary_in_public_pipeline_locations_blocks(location, payload):
    gateway = build_gateway()

    with pytest.raises(CanaryTokenDetectedError) as exc_info:
        run(gateway.process_text(payload, source_url=f"e2e://{location}"))

    assert exc_info.value.code == "CANARY_TOKEN_DETECTED"
    assert f"e2e://{location}" in exc_info.value.message
    assert DEFAULT_CANARY_TOKEN not in exc_info.value.message


def test_canary_in_browser_page_after_sanitization_blocks():
    gateway = build_gateway()
    html = f"<html><body><main>Visible page text {DEFAULT_CANARY_TOKEN}_browser</main></body></html>"
    sanitized = sanitize(html, "browser://private-profile/page")

    with pytest.raises(CanaryTokenDetectedError) as exc_info:
        run(gateway.process(sanitized, PrivacyContext(mode="full", source_url=sanitized.source_url)))

    assert exc_info.value.code == "CANARY_TOKEN_DETECTED"
    assert "browser://private-profile/page" in exc_info.value.message


def test_canary_survives_redaction_and_still_blocks():
    """PII redaction must not hide a canary leak from L7."""
    gateway = build_gateway()
    payload = f"Phone 13855551234 and canary {DEFAULT_CANARY_TOKEN}_mixed"

    with pytest.raises(CanaryTokenDetectedError):
        run(gateway.process_text(payload, source_url="e2e://mixed-pii-canary"))


def test_canary_e2e_audit_logs_masked_metadata_without_raw_text(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    gateway = build_gateway(audit_logger=audit)
    payload = f"Markdown leak {DEFAULT_CANARY_TOKEN}_audit with other text"

    with pytest.raises(CanaryTokenDetectedError):
        run(gateway.process_text(payload, mode="full", source_url="e2e://audit"))

    rows = audit.query(event_type="canary_hit", limit=10)
    assert len(rows) == 1
    row = rows[0]
    assert row["decision"] == "blocked"
    details = json.loads(row["details"])
    assert details["hit_count"] == 1
    assert details["location"] == "privacy_gateway:e2e://audit"
    assert DEFAULT_CANARY_TOKEN not in details["token"]
    assert DEFAULT_CANARY_TOKEN not in row["details"]
    assert "Markdown leak" not in row["details"]


def test_clean_end_to_end_content_passes():
    gateway = build_gateway()

    result = run(gateway.process_text("Public facts only. Contact 13855551234.", source_url="e2e://clean"))

    assert result.canary_clean is True
    assert "PII_CN_PHONE" in result.text
    assert DEFAULT_CANARY_TOKEN not in result.text
