# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

"""Crawl4AIProvider v21 - Wikipedia Anti-Bot Bypass & Exception Hierarchy"""
from __future__ import annotations
import json
import httpx
import logging
from typing import Any, Optional
from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import ExtractError, ExtractTimeout
from .base import ExtractProvider
from .models import ExtractMode, ExtractResult

logger = logging.getLogger("network.extract.crawl4ai")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def deep_clean_content(data: Any) -> str:
    if isinstance(data, str):
        if data.strip().startswith("{"):
            try: return deep_clean_content(json.loads(data))
            except: pass
        return data
    if isinstance(data, dict):
        for key in ["markdown_v2", "markdown", "fit_markdown", "text", "content", "html"]:
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
            self.api_token = cfg.api_token or "my_secret_token_1234"
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:11235").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.api_token = getattr(config, "api_token", "my_secret_token_1234")
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_token}",
                "User-Agent": DEFAULT_USER_AGENT,
            }
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(self.timeout), headers=headers, proxy=None, trust_env=False)
        return self._client

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        payload = {
            "urls": [url],
            "crawler_params": {
                "bypass_cache": True,
                "magic": True,
                "user_agent": DEFAULT_USER_AGENT,
                "headers": {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"}
            }
        }
        try:
            resp = await self.client.post("/crawl", json=payload)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            content = deep_clean_content(results[0] if results else data)
            return ExtractResult(url=url, content=content, mode=mode, extractor_used="crawl4ai")
        except httpx.TimeoutException as e:
            msg = f"Crawl4AI extraction timeout for {url}: {e}"
            logger.warning(msg)
            raise ExtractTimeout(msg)
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            msg = f"Crawl4AI HTTP error {status} for {url} (possible Wikipedia anti-bot/400 payload rejection)"
            logger.warning(msg)
            raise ExtractError(msg)
        except Exception as e:
            return ExtractResult(url=url, content="", mode=mode, error=str(e))

    async def health_check(self) -> bool:
        try: return (await self.client.get("/health")).status_code == 200
        except: return False

    async def __aenter__(self): return self
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self._client = None
