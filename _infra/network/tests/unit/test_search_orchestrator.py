"""Unit tests for MultiSourceSearchOrchestrator."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from _infra.network.exceptions import SearchResultEmpty
from _infra.network.search.base import SearchProvider
from _infra.network.search.models import SearchResult
from _infra.network.search.orchestrator import MultiSourceSearchOrchestrator, detect_intent


class FakeAPIProvider(SearchProvider):
    def __init__(self, results):
        self.search_mock = AsyncMock(return_value=results)

    async def search(self, query: str, max_results: int = 10, engines=None):
        return await self.search_mock(query, max_results=max_results, engines=engines)

    async def health_check(self) -> bool:
        return True

    def get_name(self) -> str:
        return "fake_api"


def test_detect_intent():
    assert detect_intent("python traceback async await") == "coding"
    assert detect_intent("transformer arxiv paper 2024") == "academic"
    assert detect_intent("latest release today") == "news"
    assert detect_intent("best local restaurants") == "general"


def test_orchestrator_uses_api_fallback_when_searxng_empty():
    async def run_test():
        searxng = AsyncMock()
        searxng.search.side_effect = SearchResultEmpty("empty")
        api = FakeAPIProvider([SearchResult(url="https://example.com", title="Example", score=0.8)])
        orch = MultiSourceSearchOrchestrator(searxng=searxng, api_providers=[api], min_results_threshold=1)
        results = await orch.search("query")
        assert len(results) == 1
        assert results[0].url == "https://example.com"
        api.search_mock.assert_called_once()

    asyncio.run(run_test())


def test_orchestrator_raises_when_all_sources_empty():
    async def run_test():
        searxng = AsyncMock()
        searxng.search.side_effect = SearchResultEmpty("empty")
        orch = MultiSourceSearchOrchestrator(searxng=searxng, api_providers=[], min_results_threshold=1)
        with pytest.raises(SearchResultEmpty):
            await orch.search("query")

    asyncio.run(run_test())
