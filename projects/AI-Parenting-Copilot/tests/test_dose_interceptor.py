# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 04:25:00


"""APC-T029 Dose Interceptor security tests."""

from __future__ import annotations

import pytest

from server.app.observability.audit import MemoryAuditSink
from server.app.orchestrator.dose_interceptor import DoseInterceptor


def test_llm_free_text_dose_is_intercepted() -> None:
    result = DoseInterceptor().intercept_text("可以给 2.5ml", source="llm")

    assert result.intercepted is True
    assert "2.5ml" not in result.text
    assert "剂量已拦截" in result.text


def test_rule_engine_structured_dose_text_can_pass_when_marked() -> None:
    result = DoseInterceptor().intercept_text(
        "dose_ml=2.5ml",
        source="rule_engine",
        allow_rule_engine=True,
    )

    assert result.intercepted is False
    assert result.text == "dose_ml=2.5ml"


@pytest.mark.asyncio
async def test_dose_interceptor_writes_audit_sink() -> None:
    sink = MemoryAuditSink()
    result = await DoseInterceptor().intercept_and_audit("给 1 片", source="llm", audit_sink=sink)

    assert result.intercepted is True
    assert sink.records[0].action == "dose_intercept"
