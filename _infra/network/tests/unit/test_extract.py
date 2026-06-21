"""
Unit tests for Extract module (E4-C2-S1-T1)

Covers models + ExtractProvider ABC (no real providers yet)
"""

import pytest

from _infra.network.extract.base import ExtractProvider
from _infra.network.extract.models import (
    ExtractMode,
    ExtractRequest,
    ExtractResult,
)


def test_extract_mode_enum():
    assert ExtractMode.MARKDOWN.value == "markdown"
    assert ExtractMode.SCREENSHOT.value == "screenshot"


def test_extract_request_model():
    req = ExtractRequest(
        url="https://example.com/article",
        mode=ExtractMode.MARKDOWN,
        max_chars=4000,
    )
    assert req.url.startswith("https://")
    assert req.allow_js is False


def test_extract_request_url_validation():
    with pytest.raises(ValueError):
        ExtractRequest(url="ftp://evil.com")


def test_extract_result_model():
    res = ExtractResult(
        url="https://example.com",
        content="# Hello\nWorld",
        mode=ExtractMode.MARKDOWN,
        extractor_used="crawl4ai",
    )
    assert res.char_count == 13
    assert res.mode == ExtractMode.MARKDOWN


def test_extract_provider_is_abstract():
    with pytest.raises(TypeError):
        ExtractProvider()  # type: ignore


def test_extract_result_char_count():
    res = ExtractResult(
        url="https://x.com",
        content="a" * 123,
        mode=ExtractMode.HTML_STRIPPED,
    )
    assert res.char_count == 123
