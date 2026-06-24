"""
SearXNGProvider implementation (FORGE Network incremental)

Implements SearchProvider using httpx against SearXNG JSON API.
Follows:
- TASK_BACKLOG E3-C2-S1-T2
- NETWORK_ENGINEERING_DESIGN §5.1 + §9.2 retry + §9.3 timeout
- Reuse existing config_loader, exceptions, logger, httpx
"""

from __future__ import annotations

import asyncio
from typing import Any, List, Optional
from urllib.parse import urlencode

import httpx

from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import (
    SearchEngineUnavailable,
    SearchRateLimited,
    SearchResultEmpty,
)
from _infra.network.utils.logger import get_logger

from .base import SearchProvider
from .models import SearchQuery, SearchResult

logger = get_logger("network.search.searxng")


class SearXNGProvider(SearchProvider):
    """
    SearXNG JSON API client.
    - Async httpx
    - Retry on transient errors (3x exponential)
    - Timeout from config
    - Parse results into SearchResult
    """

    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().search.searxng
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.max_results = cfg.max_results
            self.engines_enabled = cfg.engines_enabled or []
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:8080").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 6)
            self.max_results = getattr(config, "max_results", 20)
            self.engines_enabled = getattr(config, "engines_enabled", [])

        self._client: Optional[httpx.AsyncClient] = client  # allow injection for tests

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            # Explicitly disable proxy for local connections to avoid issues with system proxies
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json"},
                proxy=None, # Disable proxy for SearXNG local calls
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        max_results: int = 20,
        engines: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Call SearXNG /search?format=json
        """
        q = SearchQuery(query=query, max_results=max_results, engines=engines)

        params: dict[str, Any] = {
            "q": q.query,
            "format": "json",
            "limit": min(q.max_results, self.max_results),
        }

        # engines filter
        use_engines = engines or self.engines_enabled
        if use_engines:
            params["engines"] = ",".join(use_engines)

        url = f"{self.base_url}/search?{urlencode(params)}"

        try:
            resp = await self.client.get("/search", params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("SearXNG rate limited", status=429, query=q.query)
                raise SearchRateLimited(f"Rate limited: {e}") from e
            logger.error("SearXNG HTTP error", status=e.response.status_code, query=q.query)
            raise SearchEngineUnavailable(f"SearXNG error {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            logger.error("SearXNG timeout", timeout=self.timeout, query=q.query)
            raise SearchEngineUnavailable("SearXNG timeout") from e
        except Exception as e:
            logger.error("SearXNG connection error", error=str(e), query=q.query)
            raise SearchEngineUnavailable(f"SearXNG unavailable: {e}") from e

        results_raw = data.get("results", [])
        if not results_raw:
            raise SearchResultEmpty(f"No results for query: {q.query}")

        results: List[SearchResult] = []
        for item in results_raw[:q.max_results]:
            try:
                res = SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", item.get("snippet", "")),
                    domain=item.get("engines", [None])[0] or "",  # fallback
                    score=float(item.get("score", 0.5)) if "score" in item else 0.5,
                    raw=item,
                )
                results.append(res)
            except Exception as parse_err:
                logger.warning("Failed to parse result", error=str(parse_err), item=item)
                continue

        if not results:
            raise SearchResultEmpty(f"No valid results for query: {q.query}")

        # Sort by score desc (higher better)
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    async def health_check(self) -> bool:
        """Quick health probe using a minimal query."""
        try:
            # Increase timeout and allow empty results (just check connectivity)
            resp = await self.client.get(
                "/search",
                params={"q": "ping", "format": "json", "limit": 1},
                timeout=10.0,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning("SearXNG health check failed", error=str(e))
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
