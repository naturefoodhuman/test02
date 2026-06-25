"""
ExtractorChain (FORGE Network incremental)

降级提取链：curl_cffi(仅 TLS guarded) → Crawl4AI → trafilatura → (Playwright future)
"""

from __future__ import annotations
from typing import List, Optional
import asyncio

from .base import ExtractProvider
from .models import ExtractMode, ExtractResult
from .crawl4ai_client import Crawl4AIProvider
from .trafilatura_fallback import TrafilaturaProvider
from .curl_cffi_fallback import CurlCffiProvider

class ExtractorChain:
    def __init__(self, providers: Optional[List[ExtractProvider]] = None):
        if providers is None:
            self.providers: List[ExtractProvider] = [
                CurlCffiProvider(),
                Crawl4AIProvider(),
                TrafilaturaProvider(),
            ]
        else:
            self.providers = providers

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
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
        return ExtractResult(url=url, content="", mode=mode, extractor_used="none", 
                             error=f"All extractors failed. Last error: {last_error}")

    async def extract_batch(self, urls: List[str], mode: ExtractMode = ExtractMode.MARKDOWN) -> List[ExtractResult]:
        tasks = [self.extract(url, mode=mode) for url in urls]
        return await asyncio.gather(*tasks)

    def add_provider(self, provider: ExtractProvider, position: Optional[int] = None):
        if position is None:
            self.providers.append(provider)
        else:
            self.providers.insert(position, provider)
