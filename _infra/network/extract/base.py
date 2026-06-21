"""
ExtractProvider abstract base (ABC)

Per TASK_BACKLOG E4-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.2
Follows same style as SearchProvider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .models import ExtractRequest, ExtractResult, ExtractMode


class ExtractProvider(ABC):
    """
    职责：将 URL 转换为 LLM-ready 文本内容。
    生命周期：无状态。
    扩展：新增 Extractor 后注册到 ExtractorChain。
    """

    @abstractmethod
    async def extract(
        self,
        url: str,
        mode: ExtractMode = ExtractMode.MARKDOWN,
    ) -> ExtractResult:
        """
        Extract content from URL.

        Returns ExtractResult.
        On failure, may return result with error set or raise ExtractError.
        """
        ...

    def can_handle(self, url: str) -> bool:
        """Return True if this provider can/should handle the URL."""
        return True

    def get_name(self) -> str:
        """Provider identifier."""
        return self.__class__.__name__.replace("Provider", "").lower()
