"""Crawl4AIProvider implementation (v0.9.x compat)"""
from __future__ import annotations
import os
import json
from typing import Any, Optional
import httpx
from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import ExtractError, ExtractTimeout
from _infra.network.utils.logger import get_logger
from .base import ExtractProvider
from .models import ExtractMode, ExtractRequest, ExtractResult

logger = get_logger("network.extract.crawl4ai")

class Crawl4AIProvider(ExtractProvider):
    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().extract.crawl4ai
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.js_exec_allowed = cfg.js_exec_allowed
            self.screenshot_requires_approval = cfg.screenshot_requires_approval
            self.api_token = cfg.api_token or os.environ.get(cfg.api_token_env)
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:11235").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.js_exec_allowed = getattr(config, "js_exec_allowed", False)
            self.api_token = getattr(config, "api_token", None) or os.environ.get(getattr(config, "api_token_env", "CRAWL4AI_API_TOKEN"))

        self._client: Optional[httpx.AsyncClient] = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
                proxy=None,
            )
        return self._client

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        payload = {"urls": [url], "crawler_params": {"bypass_cache": True}}
        try:
            resp = await self.client.post("/crawl", json=payload)
            if resp.status_code == 422:
                resp = await self.client.post("/crawl", json={"url": url, "mode": "markdown"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Crawl4AI error", error=str(e), url=url)
            return ExtractResult(url=url, content="", mode=mode, error=str(e))

        # Comprehensive extraction for Crawl4AI 0.9.x
        results = data.get("results", [])
        content = ""
        if isinstance(results, list) and len(results) > 0:
            res_obj = results[0]
            # Priority list for content fields in v0.9.x
            content = (
                res_obj.get("markdown_v2") or 
                res_obj.get("markdown") or 
                res_obj.get("fit_markdown") or 
                res_obj.get("raw_markdown") or 
                res_obj.get("content") or 
                ""
            )
            # If it's a dict (e.g. structured data), try to serialize it
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
        else:
            # Legacy or other format
            content = data.get("markdown") or data.get("content") or data.get("text") or ""
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)

        return ExtractResult(url=url, content=str(content), mode=mode, extractor_used="crawl4ai", raw=data)

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/health", timeout=5.0)
            return resp.status_code == 200
        except: return False
