# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.policy import PolicyEngine


def test_policy_allows_clipboard_with_redaction():
    result = PolicyEngine(token_budget=10).check_export("token=abcdef123", gateway="clipboard", estimated_tokens=20)
    assert result.allowed is True
    assert "abcdef" not in result.redacted_text
    assert result.requires_human_review is True
    assert result.warnings == ["token budget exceeded"]


def test_policy_blocks_disabled_gateway_and_canary():
    engine = PolicyEngine()
    assert engine.check_export("hello", gateway="api").allowed is False
    assert engine.check_export("AI_CANARY_DO_NOT_LEAK_2026", gateway="clipboard").allowed is False
