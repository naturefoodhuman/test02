"""
SearchProvider abstract base (ABC)

Per TASK_BACKLOG E3-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.1
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import SearchQuery, SearchResult


class SearchProvider(ABC):
    """
    职责：执行搜索查询，返回排序后结果列表。
    生命周期：无状态，可复用。
    扩展：实现 ABC 子类，注册到 SearchProviderRegistry。
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 20,
        engines: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Execute search and return results.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            engines: Optional list of engines to use (subset of configured)

        Returns:
            List of SearchResult (sorted by score desc)
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and healthy."""
        ...

    def get_name(self) -> str:
        """Provider identifier for logging / registry."""
        return self.__class__.__name__.replace("Provider", "").lower()
