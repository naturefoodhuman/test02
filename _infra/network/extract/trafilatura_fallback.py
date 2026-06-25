# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
TrafilaturaProvider (FORGE Network incremental)

Task: E4-C3-S1-T1

Static HTML extraction fallback using trafilatura.
No browser / JS execution.
Graceful: returns empty content on failure instead of raising (per design).

Per TASK_BACKLOG + NETWORK_ENGINEERING_DESIGN §7.2
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

try:
    import trafilatura
except ImportError:
    trafilatura = None

from _infra.network.utils.logger import get_logger

from .base import ExtractProvider
from .models import ExtractMode, ExtractResult

logger = get_logger("network.extract.trafilatura")


class TrafilaturaProvider(ExtractProvider):
    """
    Pure static HTML extractor using trafilatura.
    Used as fallback when Crawl4AI fails or is unavailable.
    """

    def __init__(self, timeout_seconds: float = 8.0):
        self.available = trafilatura is not None
        self.timeout_seconds = timeout_seconds
        if not self.available:
            logger.warning("trafilatura not installed — fallback will be no-op")

    def can_handle(self, url: str) -> bool:
        # Can handle almost any public HTTP page
        return url.startswith(("http://", "https://")) and self.available

    async def _download(self, url: str) -> str:
        """Bounded async HTML download to avoid non-cancellable trafilatura threads."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        }
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds),
            follow_redirects=True,
            headers=headers,
            trust_env=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    async def extract(
        self,
        url: str,
        mode: ExtractMode = ExtractMode.MARKDOWN,
    ) -> ExtractResult:
        if not self.available:
            return ExtractResult(
                url=url,
                content="",
                mode=mode,
                extractor_used="trafilatura",
                error="trafilatura not installed",
            )

        try:
            html = await self._download(url)
            if not html:
                return ExtractResult(
                    url=url,
                    content="",
                    mode=mode,
                    extractor_used="trafilatura",
                    error="fetch failed",
                )

            if mode == ExtractMode.HTML_STRIPPED:
                content = trafilatura.extract(html, output_format="html", include_comments=False) or ""
            else:
                content = trafilatura.extract(html, output_format="markdown", include_comments=False) or ""

            return ExtractResult(
                url=url,
                content=content,
                mode=mode,
                extractor_used="trafilatura",
            )

        except httpx.TimeoutException:
            logger.warning("trafilatura extraction timeout", url=url, timeout_s=self.timeout_seconds)
            return ExtractResult(
                url=url,
                content="",
                mode=mode,
                extractor_used="trafilatura",
                error=f"timeout after {self.timeout_seconds}s",
            )
        except Exception as e:
            logger.warning("trafilatura extraction failed", url=url, error=str(e))
            return ExtractResult(
                url=url,
                content="",
                mode=mode,
                extractor_used="trafilatura",
                error=str(e),
            )

    async def health_check(self) -> bool:
        return self.available
