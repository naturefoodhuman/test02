# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.adapters.privacy_adapter import PrivacyAdapter


def test_secret_redaction_and_scan():
    adapter = PrivacyAdapter()
    result = adapter.redact("api_key=abcdef123456 password=secret")
    assert "abcdef123456" not in result.text
    assert "secret" not in result.text
    assert result.detections
    scan = adapter.scan("token=abcdef123")
    assert scan.detections


def test_canary_blocks():
    result = PrivacyAdapter().redact("AI_CANARY_DO_NOT_LEAK_2026")
    assert result.blocked is True
