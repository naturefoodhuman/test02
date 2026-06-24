# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-24 23:45:00

"""SearXNGProvider v23 - Anti-Bot CAPTCHA Risk Control & Fallback Retry Routing"""
from __future__ import annotations
import httpx
import logging
from typing import Any, List, Optional
from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import (
    SearchEngineUnavailable,
    SearchRateLimited,
    SearchResultEmpty,
)
from .base import SearchProvider
from .models import SearchQuery, SearchResult

logger = logging.getLogger("network.search.searxng")

FALLBACK_ENGINE_POOL = ["bing", "wikipedia", "github", "arxiv", "stackoverflow"]

class SearXNGProvider(SearchProvider):
    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().search.searxng
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.engines_disabled = getattr(cfg, "engines_disabled", ["google", "brave", "startpage"])
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:8090").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.engines_disabled = getattr(config, "engines_disabled", ["google", "brave", "startpage"])
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
                proxy=None,
                trust_env=False
            )
        return self._client

    async def _fetch_results(self, query: str, limit: int, engines_str: Optional[str] = None) -> tuple[List[SearchResult], List[Any]]:
        params = {"q": query, "format": "json", "limit": limit}
        if engines_str:
            params["engines"] = engines_str
        resp = await self.client.get("/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        unresponsive = data.get("unresponsive_engines", [])
        results = []
        for item in data.get("results", []):
            score = float(item.get("score", 1.0))
            results.append(SearchResult(url=item.get("url", ""), title=item.get("title", ""), snippet=item.get("content", ""), score=score))
        return results, unresponsive

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        engines_str = ",".join(engines) if engines else None
        try:
            results, unresponsive = await self._fetch_results(query, max_results, engines_str)
            
            if unresponsive:
                logger.warning(f"SearXNG upstream CAPTCHA/unresponsive detected: {unresponsive}")
                
            # 智能容错重定向重试机制：若默认引擎全报 CAPTCHA 导致空结果，自动切换稳定备用池
            if not results and engines is None:
                logger.warning("Primary engines returned empty/CAPTCHA. Auto-retrying with stable fallback engine pool...")
                fb_str = ",".join(FALLBACK_ENGINE_POOL)
                try:
                    results, unresponsive_fb = await self._fetch_results(query, max_results, fb_str)
                    if unresponsive_fb:
                        logger.warning(f"Fallback pool reported unresponsive: {unresponsive_fb}")
                except Exception as fb_err:
                    logger.debug(f"Fallback retry failed: {fb_err}")

            if not results:
                raise SearchResultEmpty(f"No search results found for query: '{query}'")
            return results
        except SearchResultEmpty:
            raise
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text_lower = e.response.text.lower()
            if status in (429, 403) or "captcha" in text_lower or "unusual traffic" in text_lower:
                msg = f"SearXNG rate limited or CAPTCHA risk control triggered: {status}"
                logger.warning(msg)
                raise SearchRateLimited(msg)
            msg = f"SearXNG HTTP error: {status}"
            logger.error(msg)
            raise SearchEngineUnavailable(msg)
        except httpx.TimeoutException as e:
            msg = f"SearXNG request timeout: {repr(e)}"
            logger.error(msg)
            raise SearchEngineUnavailable(msg)
        except Exception as e:
            msg = f"SearXNG Connection Error: {repr(e)}"
            logger.error(msg)
            raise SearchEngineUnavailable(msg)

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/search", params={"q": "ping", "format": "json", "limit": 1}, timeout=10.0)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {repr(e)}")
            return False

    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
            self._client = None
