"""Crawl4AIProvider v0.9.0+ pure text extractor"""
from __future__ import annotations
import os
import json
from typing import Any, Optional
import httpx
from _infra.network.config_loader import load_network_config
from _infra.network.utils.logger import get_logger
from .base import ExtractProvider
from .models import ExtractMode, ExtractResult

logger = get_logger("network.extract.crawl4ai")

def deep_clean_content(data: Any) -> str:
    """递归提取纯文本，拒绝 JSON 括号"""
    if isinstance(data, str):
        # 检查是否是字符串形式的 JSON
        trimmed = data.strip()
        if trimmed.startswith("{") and trimmed.endswith("}"):
            try:
                val = json.loads(trimmed)
                return deep_clean_content(val)
            except: pass
        return data
    if isinstance(data, dict):
        # 优先级：markdown_v2 > markdown > fit_markdown > text > content
        for key in ["markdown_v2", "markdown", "fit_markdown", "text", "content", "raw_markdown"]:
            if key in data and data[key]:
                return deep_clean_content(data[key])
        return ""
    if isinstance(data, list) and len(data) > 0:
        return deep_clean_content(data[0])
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
            self.api_token = getattr(config, "api_token", None) or os.environ.get(getattr(config, "api_token_env", "CRAWL4AI_API_TOKEN"))
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_token: headers["Authorization"] = f"Bearer {self.api_token}"
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(self.timeout), headers=headers, proxy=None)
        return self._client

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        payload = {"urls": [url], "crawler_params": {"bypass_cache": True}}
        try:
            resp = await self.client.post("/crawl", json=payload)
            if resp.status_code == 422:
                resp = await self.client.post("/crawl", json={"url": url, "mode": "markdown"})
            resp.raise_for_status()
            data = resp.json()
            # 兼容 0.9.x 列表结构
            results = data.get("results", [])
            raw_val = results[0] if results else data
            content = deep_clean_content(raw_val)
            return ExtractResult(url=url, content=content, mode=mode, extractor_used="crawl4ai", raw=data)
        except Exception as e:
            return ExtractResult(url=url, content="", mode=mode, error=str(e))

    async def health_check(self) -> bool:
        try: return (await self.client.get("/health")).status_code == 200
        except: return False
