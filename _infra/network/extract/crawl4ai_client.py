"""Crawl4AIProvider v19 - Async Context Manager Fixed"""
from __future__ import annotations
import os
import json
import httpx
from typing import Any, Optional
from _infra.network.config_loader import load_network_config
from .base import ExtractProvider
from .models import ExtractMode, ExtractResult

def deep_clean_content(data: Any) -> str:
    if isinstance(data, str):
        if data.strip().startswith("{"):
            try: return deep_clean_content(json.loads(data))
            except: pass
        return data
    if isinstance(data, dict):
        for key in ["markdown_v2", "markdown", "fit_markdown", "text", "content"]:
            if key in data and data[key]: return deep_clean_content(data[key])
        return ""
    if isinstance(data, list) and len(data) > 0: return deep_clean_content(data[0])
    return str(data) if data is not None else ""

class Crawl4AIProvider(ExtractProvider):
    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().extract.crawl4ai
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.api_token = cfg.api_token or os.environ.get(cfg.api_token_env)
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:11235").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.api_token = getattr(config, "api_token", None)
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_token: headers["Authorization"] = f"Bearer {self.api_token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
                proxy=None,
                trust_env=False
            )
        return self._client

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        try:
            resp = await self.client.post("/crawl", json={"urls": [url], "crawler_params": {"bypass_cache": True}})
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            content = deep_clean_content(results[0] if results else data)
            return ExtractResult(url=url, content=content, mode=mode, extractor_used="crawl4ai")
        except Exception as e:
            return ExtractResult(url=url, content="", mode=mode, error=str(e))

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/health", timeout=5.0)
            return resp.status_code == 200
        except: return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
            self._client = None
