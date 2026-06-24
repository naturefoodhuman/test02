"""
Unit tests for Search module (E3-C2-S1-T1 / T2)

- SearchQuery / SearchResult models
- SearchProvider ABC
- SearXNGProvider (mocked httpx)

Note: Async tests use asyncio.run() to avoid requiring pytest-asyncio
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from _infra.network.exceptions import (
    SearchEngineUnavailable,
    SearchRateLimited,
    SearchResultEmpty,
)
from _infra.network.search.base import SearchProvider
from _infra.network.search.models import SearchQuery, SearchResult
from _infra.network.search.searxng_client import SearXNGProvider


def test_search_query_model():
    q = SearchQuery(query="python async", max_results=10)
    assert q.query == "python async"
    assert q.max_results == 10
    assert q.language == "zh"


def test_search_query_validation():
    with pytest.raises(ValueError):
        SearchQuery(query="   ")


def test_search_result_model():
    r = SearchResult(
        url="https://example.com/foo",
        title="Example",
        snippet="Hello world",
        score=0.92,
    )
    assert r.domain == "example.com"
    assert r.score == 0.92


def test_search_result_url_validation():
    with pytest.raises(ValueError):
        SearchResult(url="not-a-url")


def test_search_provider_is_abstract():
    with pytest.raises(TypeError):
        SearchProvider()  # type: ignore


def test_searxng_search_success():
    mock_response = {
        "results": [
            {"url": "https://github.com/python/cpython", "title": "CPython", "content": "Python core", "score": 0.95},
            {"url": "https://docs.python.org", "title": "Python Docs", "content": "Official docs", "score": 0.88},
        ]
    }

    async def _run():
        # Create real httpx response mock (sync methods)
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        # get() returns the resp directly (await resolves to it)
        mock_client.get.return_value = mock_resp

        provider = SearXNGProvider(client=mock_client)

        results = await provider.search("python", max_results=5)

        assert len(results) == 2
        assert results[0].url == "https://github.com/python/cpython"
        assert results[0].score == 0.95
        assert results[0].domain == "github.com"

    asyncio.run(_run())


def test_searxng_search_empty_results():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        provider = SearXNGProvider(client=mock_client)

        with pytest.raises(SearchResultEmpty):
            await provider.search("nonexistent query xyz")

    asyncio.run(_run())


def test_searxng_search_rate_limited():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 429

        err = httpx.HTTPStatusError(
            "Too Many Requests",
            request=httpx.Request("GET", "http://example"),
            response=mock_resp,
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = err

        provider = SearXNGProvider(client=mock_client)

        with pytest.raises(SearchRateLimited):
            await provider.search("test")

    asyncio.run(_run())


def test_searxng_search_timeout():
    async def _run():
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        provider = SearXNGProvider(client=mock_client)

        with pytest.raises(SearchEngineUnavailable):
            await provider.search("test")

    asyncio.run(_run())


def test_searxng_health_check_ok():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"url": "https://x"}]}
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        provider = SearXNGProvider(client=mock_client)
        healthy = await provider.health_check()
        assert healthy is True

    asyncio.run(_run())


def test_searxng_health_check_fail():
    async def _run():
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.ConnectError("refused")

        provider = SearXNGProvider(client=mock_client)
        healthy = await provider.health_check()
        assert healthy is False

    asyncio.run(_run())


def test_search_result_domain_fallback():
    r = SearchResult(url="https://www.Example.COM/path?q=1", title="x")
    assert r.domain == "www.example.com"


def test_searxng_search_auto_fallback_on_captcha():
    async def _run():
        resp1 = MagicMock(spec=httpx.Response)
        resp1.status_code = 200
        resp1.json.return_value = {"results": [], "unresponsive_engines": [["duckduckgo", "CAPTCHA"]]}
        resp1.raise_for_status.return_value = None

        resp2 = MagicMock(spec=httpx.Response)
        resp2.status_code = 200
        resp2.json.return_value = {"results": [{"url": "https://wikipedia.org/wiki/LangGraph", "title": "LangGraph", "content": "summary", "score": 0.95}]}
        resp2.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp1, resp2]

        provider = SearXNGProvider(client=mock_client)
        results = await provider.search("langgraph")

        assert len(results) == 1
        assert results[0].domain == "wikipedia.org"
        assert mock_client.get.call_count == 2

    asyncio.run(_run())
