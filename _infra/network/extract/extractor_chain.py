"""
ExtractorChain (FORGE Network incremental)

降级提取链：Crawl4AI → trafilatura → (Playwright future)

Per TASK_BACKLOG E4 + NETWORK_ENGINEERING_DESIGN §5.2

Simple priority chain. First successful result wins.
"""

from __future__ import annotations

from typing import List, Optional

from .base import ExtractProvider
from .models import ExtractMode, ExtractResult
from .crawl4ai_client import Crawl4AIProvider
from .trafilatura_fallback import TrafilaturaProvider


class ExtractorChain:
    """
    按 can_handle + 优先级依次尝试：
    Crawl4AI (primary) → trafilatura → Playwright (future)
    任一成功则返回，全失败则返回带 error 的结果。
    """

    def __init__(self, providers: Optional[List[ExtractProvider]] = None):
        if providers is None:
            # Default production chain (order matters)
            self.providers: List[ExtractProvider] = [
                Crawl4AIProvider(),
                TrafilaturaProvider(),
                # PlaywrightProvider() will be appended later when ready
            ]
        else:
            self.providers = providers

    async def extract(
        self,
        url: str,
        mode: ExtractMode = ExtractMode.MARKDOWN,
    ) -> ExtractResult:
        last_error: Optional[str] = None

        for provider in self.providers:
            if not provider.can_handle(url):
                continue

            try:
                result = await provider.extract(url, mode=mode)
                if result.content and not result.error:
                    result.extractor_used = provider.get_name()
                    return result
                else:
                    last_error = result.error or "empty content"
            except Exception as exc:
                last_error = str(exc)
                continue

        # All failed
        return ExtractResult(
            url=url,
            content="",
            mode=mode,
            extractor_used="none",
            error=f"All extractors failed. Last error: {last_error}",
        )

    async def extract_batch(
        self,
        urls: List[str],
        mode: ExtractMode = ExtractMode.MARKDOWN,
    ) -> List[ExtractResult]:
        """Parallel extraction for multiple URLs."""
        import asyncio
        tasks = [self.extract(url, mode=mode) for url in urls]
        return await asyncio.gather(*tasks)

    def add_provider(self, provider: ExtractProvider, position: Optional[int] = None):
        """Allow runtime extension of the chain."""
        if position is None:
            self.providers.append(provider)
        else:
            self.providers.insert(position, provider)
