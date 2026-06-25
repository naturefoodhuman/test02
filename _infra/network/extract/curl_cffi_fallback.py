# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
TLS-impersonating extractor fallback using curl_cffi when available.

This provider is intentionally narrow: it only handles known TLS-guarded public
sites and only when curl_cffi is installed. It does not replace Crawl4AI as the
primary extractor.
"""

from __future__ import annotations

from urllib.parse import urlparse

from _infra.network.utils.logger import get_logger

from .base import ExtractProvider
from .models import ExtractMode, ExtractResult

logger = get_logger("network.extract.curl_cffi")

try:  # optional dependency
    from curl_cffi.requests import AsyncSession

    CURL_CFFI_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent optional dependency
    AsyncSession = None  # type: ignore[assignment]
    CURL_CFFI_AVAILABLE = False

TLS_GUARDED_DOMAINS = (
    "cloudflare.com",
    "vercel.app",
    "fly.dev",
    "patreon.com",
    "medium.com",
)


class CurlCffiProvider(ExtractProvider):
    """Extract public pages using browser-like TLS fingerprints when needed."""

    def __init__(
        self,
        proxy: str = "http://host.docker.internal:7890",
        timeout: int = 25,
        impersonate: str = "chrome131",
    ) -> None:
        self.proxy = proxy
        self.timeout = timeout
        self.impersonate = impersonate

    def can_handle(self, url: str) -> bool:
        if not CURL_CFFI_AVAILABLE:
            return False
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return False
        return any(host == d or host.endswith("." + d) for d in TLS_GUARDED_DOMAINS)

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        if not CURL_CFFI_AVAILABLE or AsyncSession is None:
            return ExtractResult(url=url, content="", mode=mode, extractor_used="curl_cffi", error="curl_cffi unavailable")
        try:
            async with AsyncSession(
                impersonate=self.impersonate,
                proxy=self.proxy,
                timeout=self.timeout,
            ) as session:
                resp = await session.get(url, allow_redirects=True)
                if resp.status_code != 200:
                    return ExtractResult(
                        url=url,
                        content="",
                        mode=mode,
                        extractor_used="curl_cffi",
                        error=f"HTTP {resp.status_code}",
                    )
                html = resp.text
                try:
                    import trafilatura

                    content = trafilatura.extract(html, include_comments=False, include_tables=True) or html[:8000]
                except Exception:
                    content = html[:8000]
                return ExtractResult(url=url, content=content, mode=mode, extractor_used="curl_cffi")
        except Exception as exc:
            logger.warning("curl_cffi extraction failed", url=url, error=repr(exc))
            return ExtractResult(url=url, content="", mode=mode, extractor_used="curl_cffi", error=str(exc))
