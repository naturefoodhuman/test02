# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
External Search API Providers - optional fallback layer.

Providers are loaded only when their API key environment variables are present.
No key is stored in the repository. These providers implement the existing
SearchProvider interface and are used only after the local SearXNG tiered route
cannot satisfy the minimum result threshold.
"""

from __future__ import annotations

import os
from typing import List, Optional

import httpx

from .base import SearchProvider
from .models import SearchResult


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _default_proxy() -> Optional[str]:
    """Proxy for search APIs; empty env value disables proxy explicitly."""
    raw = os.getenv("NETWORK_SEARCH_API_PROXY")
    if raw is not None:
        return raw or None
    return "http://127.0.0.1:7890"


class BraveSearchAPIProvider(SearchProvider):
    """Brave Search API fallback provider."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15, proxy: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY required")
        self.timeout = timeout
        self.proxy = _default_proxy() if proxy is None else proxy
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.search.brave.com/res/v1",
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
                proxy=self.proxy,
                trust_env=False,
            )
        return self._client

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        resp = await self.client.get(
            "/web/search",
            params={"q": query, "count": min(max_results, 20), "safesearch": "off"},
        )
        resp.raise_for_status()
        data = resp.json()
        web = data.get("web", {}).get("results", [])
        return [
            SearchResult(
                url=r["url"],
                title=r.get("title", ""),
                snippet=r.get("description", ""),
                score=_clamp_score(1.0 - i * 0.05),
                raw={"source": "brave_api"},
            )
            for i, r in enumerate(web)
            if r.get("url")
        ]

    async def health_check(self) -> bool:
        try:
            r = await self.client.get("/web/search", params={"q": "ping", "count": 1}, timeout=8.0)
            return r.status_code == 200
        except Exception:
            return False

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class TavilySearchAPIProvider(SearchProvider):
    """Tavily API fallback provider."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 20, proxy: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY required")
        self.timeout = timeout
        self.proxy = _default_proxy() if proxy is None else proxy
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.tavily.com",
                timeout=httpx.Timeout(self.timeout),
                proxy=self.proxy,
                trust_env=False,
            )
        return self._client

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        resp = await self.client.post(
            "/search",
            json={
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            SearchResult(
                url=r["url"],
                title=r.get("title", ""),
                snippet=r.get("content", ""),
                score=_clamp_score(float(r.get("score", 0.5) or 0.5)),
                raw={"source": "tavily_api"},
            )
            for r in data.get("results", [])
            if r.get("url")
        ]

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class SerperAPIProvider(SearchProvider):
    """Serper.dev Google-compatible API fallback provider."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15, proxy: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY required")
        self.timeout = timeout
        self.proxy = _default_proxy() if proxy is None else proxy
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://google.serper.dev",
                timeout=httpx.Timeout(self.timeout),
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                proxy=self.proxy,
                trust_env=False,
            )
        return self._client

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        resp = await self.client.post("/search", json={"q": query, "num": max_results})
        resp.raise_for_status()
        data = resp.json()
        organic = data.get("organic", [])
        return [
            SearchResult(
                url=r["link"],
                title=r.get("title", ""),
                snippet=r.get("snippet", ""),
                score=_clamp_score(1.0 - i * 0.05),
                raw={"source": "serper_api"},
            )
            for i, r in enumerate(organic)
            if r.get("link")
        ]

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
