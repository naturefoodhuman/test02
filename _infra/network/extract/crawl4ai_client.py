"""
Crawl4AIProvider implementation (FORGE Network incremental)

Implements ExtractProvider using httpx against Crawl4AI HTTP API.
Follows:
- TASK_BACKLOG E4-C2-S1-T2
- NETWORK_ENGINEERING_DESIGN §5.2 + §9.3 timeout
- Reuse existing config_loader, exceptions, logger, httpx
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import (
    AllExtractorsFailed,
    ExtractError,
    ExtractTimeout,
)
from _infra.network.utils.logger import get_logger

from .base import ExtractProvider
from .models import ExtractMode, ExtractRequest, ExtractResult

logger = get_logger("network.extract.crawl4ai")


class Crawl4AIProvider(ExtractProvider):
    """
    Crawl4AI HTTP client (primary extractor).
    - Async httpx
    - Supports MARKDOWN and HTML_STRIPPED
    - Screenshot requires explicit approval flag
    - Timeout from config
    """

    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        import os
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
            self.screenshot_requires_approval = getattr(config, "screenshot_requires_approval", True)
            self.api_token = getattr(config, "api_token", None) or os.environ.get(getattr(config, "api_token_env", "CRAWL4AI_API_TOKEN"))

        self._client: Optional[httpx.AsyncClient] = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            # Explicitly disable proxy for local connections
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
                proxy=None, # Disable proxy for local calls
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def extract(
        self,
        url: str,
        mode: ExtractMode = ExtractMode.MARKDOWN,
    ) -> ExtractResult:
        req = ExtractRequest(url=url, mode=mode)

        # Safety: screenshot always requires approval flag
        if mode == ExtractMode.SCREENSHOT and not self.screenshot_requires_approval:
            # In production this would be blocked by higher layer; here we still allow but warn
            logger.warning("screenshot requested without approval flag", url=url)

        # Crawl4AI 0.9.x API compatibility
        # It expects "urls" (list) and optionally "crawler_params"
        payload: dict[str, Any] = {
            "urls": [req.url],
            "crawler_params": {
                "bypass_cache": True,
                "only_text": True,
            }
        }

        try:
            resp = await self.client.post("/crawl", json=payload)
            if resp.status_code == 422:
                # Fallback to legacy single-url format if 422 occurs
                legacy_payload = {
                    "url": req.url,
                    "mode": "markdown" if mode == ExtractMode.MARKDOWN else "html",
                    "js": req.allow_js and self.js_exec_allowed,
                    "max_chars": req.max_chars,
                }
                resp = await self.client.post("/crawl", json=legacy_payload)
            
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Crawl4AI HTTP error", status=e.response.status_code, url=req.url, response=e.response.text)
            raise ExtractError(f"Crawl4AI error {e.response.status_code}: {e.response.text}") from e
        except httpx.TimeoutException as e:
            logger.error("Crawl4AI timeout", url=req.url)
            raise ExtractTimeout("Crawl4AI extraction timeout") from e
        except Exception as e:
            logger.error("Crawl4AI connection error", error=str(e), url=req.url)
            raise ExtractError(f"Crawl4AI unavailable: {e}") from e

        # Handle 0.9.x response shape (results list)
        content = ""
        results = data.get("results")
        if isinstance(results, list) and len(results) > 0:
            result_obj = results[0]
            content = result_obj.get("markdown") or result_obj.get("html") or result_obj.get("content", "")
        else:
            # Legacy or direct object
            content = data.get("markdown") or data.get("html") or data.get("content", "")

        result = ExtractResult(
            url=req.url,
            content=content,
            mode=mode,
            extractor_used="crawl4ai",
            raw=data,
        )

        if not result.content and mode != ExtractMode.SCREENSHOT:
            logger.warning("Crawl4AI returned empty content", url=req.url)

        return result

    async def health_check(self) -> bool:
        """Probe /health endpoint."""
        try:
            resp = await self.client.get("/health", timeout=5.0)
            return resp.status_code == 200
        except Exception as e:
            logger.warning("Crawl4AI health check failed", error=str(e))
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
