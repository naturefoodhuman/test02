"""
Unit tests for SearchCache (E3-C4-S1-T1)
"""

import time

from _infra.network.search.cache import SearchCache
from _infra.network.search.models import SearchResult


def test_cache_set_get_roundtrip():
    cache = SearchCache(db_path=":memory:")
    results = [
        SearchResult(url="https://github.com/foo", title="Foo", score=0.95),
        SearchResult(url="https://example.com/bar", title="Bar", score=0.8),
    ]

    cache.set("python async", results, max_results=10, language="en")
    got = cache.get("python async", max_results=10, language="en")

    assert got is not None
    assert len(got) == 2
    assert got[0].url == "https://github.com/foo"


def test_cache_expiration():
    cache = SearchCache(db_path=":memory:", default_ttl=1)  # 1 second TTL
    res = [SearchResult(url="https://x.com", title="x", score=0.5)]

    cache.set("short lived", res, max_results=5)
    assert cache.get("short lived", max_results=5) is not None

    time.sleep(1.1)
    assert cache.get("short lived", max_results=5) is None


def test_cache_lru_eviction():
    cache = SearchCache(db_path=":memory:", max_size=2)

    r1 = [SearchResult(url="https://a.com", score=0.1)]
    r2 = [SearchResult(url="https://b.com", score=0.2)]
    r3 = [SearchResult(url="https://c.com", score=0.3)]

    cache.set("q1", r1, max_results=1)
    cache.set("q2", r2, max_results=1)
    cache.set("q3", r3, max_results=1)  # should evict oldest (q1)

    assert cache.get("q1", max_results=1) is None
    assert cache.get("q2", max_results=1) is not None
    assert cache.get("q3", max_results=1) is not None


def test_cache_clear_expired():
    cache = SearchCache(db_path=":memory:", default_ttl=1)
    cache.set("old", [SearchResult(url="https://old.com", score=0.1)], max_results=1)
    time.sleep(1.1)
    deleted = cache.clear_expired()
    assert deleted >= 1
    assert cache.get("old", max_results=1) is None


def test_cache_different_keys():
    cache = SearchCache(db_path=":memory:")
    r = [SearchResult(url="https://x.com", score=0.9)]

    cache.set("query1", r, max_results=5)
    cache.set("query1", r, max_results=10)  # different max_results → different key

    # They should be stored separately
    assert cache.get("query1", max_results=5) is not None
    assert cache.get("query1", max_results=10) is not None
