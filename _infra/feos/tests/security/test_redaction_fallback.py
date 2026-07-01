# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.policy.redaction import RegexRedactor


def test_private_key_redacted():
    text = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"
    result = RegexRedactor().redact(text)
    assert "PRIVATE KEY" not in result.text
    assert result.detections[0].type == "private_key"
