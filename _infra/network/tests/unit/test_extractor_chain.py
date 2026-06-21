"""
Unit tests for ExtractorChain (M2 extract)

Uses mocked providers for isolation.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from _infra.network.extract.base import ExtractProvider
from _infra.network.extract.extractor_chain import ExtractorChain
from _infra.network.extract.models import ExtractMode, ExtractResult


class MockProvider(ExtractProvider):
    def __init__(self, name: str, content: str = "", error: str | None = None):
        self._name = name
        self._content = content
        self._error = error

    async def extract(self, url: str, mode=ExtractMode.MARKDOWN):
        if self._error:
            return ExtractResult(url=url, content="", mode=mode, extractor_used=self._name, error=self._error)
        return ExtractResult(url=url, content=self._content, mode=mode, extractor_used=self._name)

    def get_name(self):
        return self._name

    def can_handle(self, url):
        return True


def test_chain_falls_back():
    async def _run():
        p1 = MockProvider("crawl4ai", error="failed")
        p2 = MockProvider("trafilatura", content="# Good content from fallback")

        chain = ExtractorChain(providers=[p1, p2])
        result = await chain.extract("https://example.com")

        assert result.extractor_used == "trafilatura"
        assert "Good content" in result.content

    asyncio.run(_run())


def test_chain_returns_error_when_all_fail():
    async def _run():
        p1 = MockProvider("crawl4ai", error="boom")
        p2 = MockProvider("trafilatura", error="also boom")

        chain = ExtractorChain(providers=[p1, p2])
        result = await chain.extract("https://bad.com")

        assert result.error is not None
        assert "All extractors failed" in result.error

    asyncio.run(_run())


def test_chain_prefers_first_success():
    async def _run():
        p1 = MockProvider("crawl4ai", content="Primary success")
        p2 = MockProvider("trafilatura", content="Fallback")

        chain = ExtractorChain(providers=[p1, p2])
        result = await chain.extract("https://example.com")

        assert result.extractor_used == "crawl4ai"
        assert "Primary" in result.content

    asyncio.run(_run())
