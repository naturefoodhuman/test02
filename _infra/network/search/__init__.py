# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
Search module (FORGE Network incremental)

Exports:
- SearchQuery, SearchResult
- SearchProvider (ABC)
- SearXNGProvider
- MultiSourceSearchOrchestrator
- EngineCircuitBreaker
- normalize_url, rank_search_results
"""

from .base import SearchProvider
from .circuit_breaker import EngineCircuitBreaker, EngineState, get_global_breaker
from .models import SearchQuery, SearchResult
from .orchestrator import MultiSourceSearchOrchestrator, detect_intent
from .result_scorer import rank_search_results, score_domain
from .searxng_client import SearXNGProvider
from .url_normalizer import is_same_url, normalize_url

__all__ = [
    "SearchQuery",
    "SearchResult",
    "SearchProvider",
    "SearXNGProvider",
    "MultiSourceSearchOrchestrator",
    "detect_intent",
    "EngineCircuitBreaker",
    "EngineState",
    "get_global_breaker",
    "normalize_url",
    "is_same_url",
    "score_domain",
    "rank_search_results",
]
