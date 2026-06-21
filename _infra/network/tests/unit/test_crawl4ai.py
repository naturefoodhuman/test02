"""
Unit tests for Crawl4AIProvider (E4-C2-S1-T2)

Uses MagicMock + AsyncMock pattern (consistent with search tests).
No real service required.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from _infra.network.exceptions import ExtractError, ExtractTimeout
from _infra.network.extract.crawl4ai_client import Crawl4AIProvider
from _infra.network.extract.models import ExtractMode


def test_crawl4ai_provider_basic():
    provider = Crawl4AIProvider()
    assert provider.get_name() == "crawl4ai"
    assert provider.can_handle("https://example.com") is True


def test_crawl4ai_extract_success_markdown():
    mock_data = {
        "markdown": "# Title\n\nThis is extracted content from Crawl4AI.",
        "url": "https://example.com/article",
        "status": "success",
    }

    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_resp

        provider = Crawl4AIProvider(client=mock_client)
        result = await provider.extract("https://example.com/article", mode=ExtractMode.MARKDOWN)

        assert result.extractor_used == "crawl4ai"
        assert "Title" in result.content
        assert result.mode == ExtractMode.MARKDOWN
        assert result.char_count > 10

    asyncio.run(_run())


def test_crawl4ai_extract_html_stripped():
    mock_data = {"html": "<h1>Stripped</h1><p>Content</p>", "url": "https://ex.com"}

    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_resp

        provider = Crawl4AIProvider(client=mock_client)
        result = await provider.extract("https://ex.com", mode=ExtractMode.HTML_STRIPPED)

        assert "Stripped" in result.content
        assert result.mode == ExtractMode.HTML_STRIPPED

    asyncio.run(_run())


def test_crawl4ai_extract_timeout():
    async def _run():
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = httpx.TimeoutException("timeout")

        provider = Crawl4AIProvider(client=mock_client)

        with pytest.raises(ExtractTimeout):
            await provider.extract("https://slow.com")

    asyncio.run(_run())


def test_crawl4ai_extract_http_error():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 500
        err = httpx.HTTPStatusError("Server error", request=httpx.Request("POST", ""), response=mock_resp)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = err

        provider = Crawl4AIProvider(client=mock_client)

        with pytest.raises(ExtractError):
            await provider.extract("https://bad.com")

    asyncio.run(_run())


def test_crawl4ai_health_check():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        provider = Crawl4AIProvider(client=mock_client)
        healthy = await provider.health_check()
        assert healthy is True

    asyncio.run(_run())


def test_crawl4ai_health_check_fail():
    async def _run():
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.ConnectError("refused")

        provider = Crawl4AIProvider(client=mock_client)
        healthy = await provider.health_check()
        assert healthy is False

    asyncio.run(_run())
