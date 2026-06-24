"""SearXNGProvider v18 - Final No-Proxy Fix"""
from __future__ import annotations
import httpx
from typing import Any, List, Optional
from _infra.network.config_loader import load_network_config
from .base import SearchProvider
from .models import SearchQuery, SearchResult

class SearXNGProvider(SearchProvider):
    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().search.searxng
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:8090").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            # 双重保险：trust_env=False + proxy=None
            # 彻底解决终端全局代理导致无法连接 127.0.0.1 的 404/ConnectionError 问题
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json"},
                proxy=None,
                trust_env=False
            )
        return self._client

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        params = {"q": query, "format": "json", "limit": max_results}
        if engines: params["engines"] = ",".join(engines)
        try:
            resp = await self.client.get("/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append(SearchResult(url=item.get("url", ""), title=item.get("title", ""), snippet=item.get("content", ""), score=1.0))
            return results
        except Exception as e:
            raise RuntimeError(f"SearXNG connection error: {e}")

    async def health_check(self) -> bool:
        try: return (await self.client.get("/search", params={"q": "ping", "format": "json", "limit": 1}, timeout=5.0)).status_code == 200
        except: return False
    async def __aenter__(self): return self
    async def __aexit__(self, *args): await self.client.aclose()
