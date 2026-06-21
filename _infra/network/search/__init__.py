"""
Search module (FORGE Network incremental)

Exports:
- SearchQuery, SearchResult
- SearchProvider (ABC)
- SearXNGProvider
- normalize_url, rank_search_results
"""

from .models import SearchQuery, SearchResult
from .base import SearchProvider
from .searxng_client import SearXNGProvider
from .url_normalizer import normalize_url, is_same_url
from .result_scorer import score_domain, rank_search_results

__all__ = [
    "SearchQuery",
    "SearchResult",
    "SearchProvider",
    "SearXNGProvider",
    "normalize_url",
    "is_same_url",
    "score_domain",
    "rank_search_results",
]
