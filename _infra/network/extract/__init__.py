"""
Extract module (FORGE Network incremental)

M-04: Content extraction layer
- Crawl4AI primary
- trafilatura + Playwright fallbacks

Exports:
- ExtractRequest, ExtractResult, ExtractMode
- ExtractProvider (ABC)
- Crawl4AIProvider, TrafilaturaProvider
- ExtractorChain, clean_markdown
"""

from .models import ExtractRequest, ExtractResult, ExtractMode
from .base import ExtractProvider
from .crawl4ai_client import Crawl4AIProvider
from .trafilatura_fallback import TrafilaturaProvider
from .extractor_chain import ExtractorChain
from .markdown_cleaner import clean_markdown, clean_extract_result, chunk_markdown

__all__ = [
    "ExtractRequest",
    "ExtractResult",
    "ExtractMode",
    "ExtractProvider",
    "Crawl4AIProvider",
    "TrafilaturaProvider",
    "ExtractorChain",
    "clean_markdown",
    "clean_extract_result",
    "chunk_markdown",
]
