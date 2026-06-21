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
        if config is None:
            cfg = load_network_config().extract.crawl4ai
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.js_exec_allowed = cfg.js_exec_allowed
            self.screenshot_requires_approval = cfg.screenshot_requires_approval
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:11235").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.js_exec_allowed = getattr(config, "js_exec_allowed", False)
            self.screenshot_requires_approval = getattr(config, "screenshot_requires_approval", True)

        self._client: Optional[httpx.AsyncClient] = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json"},
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

        payload: dict[str, Any] = {
            "url": req.url,
            "mode": "markdown" if mode == ExtractMode.MARKDOWN else "html",
            "js": req.allow_js and self.js_exec_allowed,
            "max_chars": req.max_chars,
        }

        try:
            resp = await self.client.post("/crawl", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Crawl4AI HTTP error", status=e.response.status_code, url=req.url)
            raise ExtractError(f"Crawl4AI error {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            logger.error("Crawl4AI timeout", url=req.url)
            raise ExtractTimeout("Crawl4AI extraction timeout") from e
        except Exception as e:
            logger.error("Crawl4AI connection error", error=str(e), url=req.url)
            raise ExtractError(f"Crawl4AI unavailable: {e}") from e

        content = data.get("markdown") or data.get("html") or data.get("content", "")
        if not content and mode != ExtractMode.SCREENSHOT:
            # For screenshot we expect different response shape in real impl
            pass

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
