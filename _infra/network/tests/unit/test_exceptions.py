# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:07:00 CST

"""单元测试：统一异常体系"""

import pytest

from _infra.network.exceptions import (
    NetworkError,
    SearchEngineUnavailable,
    PIIDetectedError,
    PolicyDeniedError,
    CanaryTokenDetectedError,
    AllExtractorsFailed,
)


def test_base_exception():
    exc = NetworkError("base error", code="TEST_001", foo="bar")
    assert exc.code == "TEST_001"
    assert "base error" in str(exc)
    assert exc.details.get("foo") == "bar"


def test_search_error():
    exc = SearchEngineUnavailable("SearXNG down")
    assert exc.code == "SEARCH_ENGINE_UNAVAILABLE"
    assert "SearXNG" in str(exc)


def test_privacy_pii_error():
    detections = [{"type": "CN_PHONE", "value": "138****1234"}]
    exc = PIIDetectedError(detections)
    assert exc.code == "PII_DETECTED"
    assert len(exc.detections) == 1


def test_mcp_policy_denied():
    exc = PolicyDeniedError("execute_js", "high risk action")
    assert exc.code == "MCP_POLICY_DENIED"
    assert "execute_js" in str(exc)


def test_canary_token():
    exc = CanaryTokenDetectedError("AI_CANARY_2026", "markdown")
    assert exc.code == "CANARY_TOKEN_DETECTED"
    assert "AI_CANARY" in str(exc)


def test_extract_all_failed():
    exc = AllExtractorsFailed("Crawl4AI + trafilatura + playwright all failed")
    assert exc.code == "ALL_EXTRACTORS_FAILED"
