# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:58:00

"""Unit and security tests for CanaryTokenMonitor (E5-C8-S1-T1)."""

import json

import pytest

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.exceptions import CanaryTokenDetectedError
from _infra.network.privacy_gateway.canary import CanaryTokenMonitor, DEFAULT_CANARY_TOKEN


def test_scan_detects_default_canary_with_suffix():
    monitor = CanaryTokenMonitor()
    text = "leaked AI_CANARY_DO_NOT_LEAK_2026_abc123 in output"

    hits = monitor.scan(text, location="output_markdown")

    assert len(hits) == 1
    assert hits[0].token == "AI_CANARY_DO_NOT_LEAK_2026_abc123"
    assert hits[0].location == "output_markdown"
    assert hits[0].start == text.index("AI_CANARY")


def test_scan_detects_exact_configured_token():
    monitor = CanaryTokenMonitor(tokens=["CUSTOM_CANARY_TOKEN"])

    hits = monitor.scan("prefix CUSTOM_CANARY_TOKEN suffix")

    assert len(hits) == 1
    assert hits[0].token == "CUSTOM_CANARY_TOKEN"


def test_scan_supports_wildcard_token_config():
    monitor = CanaryTokenMonitor(tokens=["LEAK_TEST_*"])

    assert monitor.has_canary("value LEAK_TEST_abc-123") is True
    assert monitor.has_canary("value LEAK_SAFE_abc-123") is False


def test_clean_text_passes():
    monitor = CanaryTokenMonitor()
    monitor.assert_clean("ordinary redacted output", location="unit")


def test_assert_clean_blocks_on_canary():
    monitor = CanaryTokenMonitor()

    with pytest.raises(CanaryTokenDetectedError) as exc_info:
        monitor.assert_clean(f"bad {DEFAULT_CANARY_TOKEN}_x", location="claude_transcript")

    assert exc_info.value.code == "CANARY_TOKEN_DETECTED"
    assert "claude_transcript" in exc_info.value.message
    assert DEFAULT_CANARY_TOKEN not in exc_info.value.message  # masked in exception


def test_audit_log_records_masked_hit_without_raw_text(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    monitor = CanaryTokenMonitor(audit_logger=audit, mode="private")

    with pytest.raises(CanaryTokenDetectedError):
        monitor.assert_clean(f"bad {DEFAULT_CANARY_TOKEN}_secret", location="browser_logs")

    rows = audit.query(event_type="canary_hit", limit=5)
    assert len(rows) == 1
    assert rows[0]["decision"] == "blocked"
    assert rows[0]["mode"] == "private"
    details = json.loads(rows[0]["details"])
    assert details["location"] == "browser_logs"
    assert details["hit_count"] == 1
    assert DEFAULT_CANARY_TOKEN not in details["token"]
    assert "bad" not in rows[0]["details"]  # full source text is never logged


def test_from_config_reads_yaml_and_network_config(tmp_path, monkeypatch):
    config = tmp_path / "canary_tokens.yaml"
    config.write_text(
        "canary_tokens:\n  - YAML_CANARY\ncanary_patterns:\n  - 'REGEX_CANARY_[0-9]+'\n",
        encoding="utf-8",
    )

    monitor = CanaryTokenMonitor.from_config(config_path=config)

    assert monitor.has_canary("YAML_CANARY") is True
    assert monitor.has_canary("REGEX_CANARY_123") is True


def test_multiple_hits_sorted_by_offset():
    monitor = CanaryTokenMonitor(tokens=["FIRST_CANARY", "SECOND_CANARY"])
    hits = monitor.scan("SECOND_CANARY then FIRST_CANARY")

    assert [hit.token for hit in hits] == ["SECOND_CANARY", "FIRST_CANARY"]
    assert hits[0].start < hits[1].start
