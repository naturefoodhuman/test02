"""
Unit tests for Markdown Cleaner (E4-C2-S1-T3)
"""

import pytest

from _infra.network.extract.markdown_cleaner import (
    chunk_markdown,
    clean_markdown,
    clean_extract_result,
)
from _infra.network.extract.models import ExtractMode, ExtractResult


def test_clean_collapses_blank_lines():
    raw = "Line1\n\n\n\nLine2\n\n\nLine3"
    cleaned = clean_markdown(raw)
    assert cleaned.count("\n\n") <= 2
    assert "Line1" in cleaned
    assert "Line3" in cleaned


def test_clean_removes_ads():
    raw = "Good content\n\n[广告]\n\nMore content\n赞助内容 here"
    cleaned = clean_markdown(raw, remove_ads=True)
    assert "广告" not in cleaned
    assert "赞助内容" not in cleaned
    assert "Good content" in cleaned


def test_clean_truncates():
    long = "x" * 10000
    cleaned = clean_markdown(long, max_chars=500)
    assert len(cleaned) <= 520  # approx with truncation note
    assert "truncated" in cleaned


def test_clean_extract_result():
    res = ExtractResult(
        url="https://ex.com",
        content="Title\n\n\n\n[广告]\n\nBody",
        mode=ExtractMode.MARKDOWN,
    )
    cleaned = clean_extract_result(res, max_chars=100)
    assert cleaned.char_count <= 100
    assert "广告" not in cleaned.content


def test_chunk_markdown():
    text = "a" * 10000
    chunks = chunk_markdown(text, chunk_size=3000, overlap=200)
    assert len(chunks) > 3
    assert all(len(c) <= 3000 + 10 for c in chunks)
