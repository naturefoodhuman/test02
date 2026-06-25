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

import asyncio
from typing import Any, Optional

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
            # trafilatura is synchronous and may block for ~30s on sites that are
            # unreachable from the user's proxy. Bound it so NetworkWorkflow can
            # quickly fall back to search snippets instead of waiting minutes.
            downloaded = await asyncio.wait_for(
                asyncio.to_thread(trafilatura.fetch_url, url),
                timeout=self.timeout_seconds,
            )
            if not downloaded:
                return ExtractResult(
                    url=url,
                    content="",
                    mode=mode,
                    extractor_used="trafilatura",
                    error="fetch failed",
                )

            if mode == ExtractMode.HTML_STRIPPED:
                # Return cleaned HTML
                content = trafilatura.extract(downloaded, output_format="html", include_comments=False) or ""
            else:
                # Default to markdown
                content = trafilatura.extract(downloaded, output_format="markdown", include_comments=False) or ""

            result = ExtractResult(
                url=url,
                content=content,
                mode=mode,
                extractor_used="trafilatura",
            )
            return result

        except asyncio.TimeoutError:
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
