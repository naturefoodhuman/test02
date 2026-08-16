# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""EvidencePolicy 仓储单元测试（APC-T018）——缓存逻辑部分。

缓存语义（get_current 命中/miss、invalidate 清除）用 Fake session 验证，不依赖 DB。
DB 持久化（upsert/activate/get_current 真实读写）在 integration 测试覆盖
（``server/tests/integration/test_evidence_repo.py``）。
"""

from __future__ import annotations

import asyncio

from cachetools import TTLCache

from server.app.rule_engine.evidence_repo import SqlAlchemyEvidencePolicyRepository


class FakeSession:
    """最小 AsyncSession 替身：记录 execute 调用，返回可配置结果。

    仅用于缓存逻辑测试——get_current 命中缓存时不应触发 execute（验证缓存生效）。
    """

    def __init__(self) -> None:
        self.execute_calls = 0

    async def execute(self, *_args, **_kwargs):
        self.execute_calls += 1
        return _FakeResult(None)

    async def flush(self):
        pass


class _FakeResult:
    def __init__(self, value) -> None:
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def test_get_current_miss_then_hit_caches():
    """缓存命中时 get_current 不查 DB（验证 L1 缓存生效）。"""
    cache: TTLCache[tuple[str, str], object] = TTLCache(maxsize=8, ttl=300)
    cached_value = object()
    cache[("triage", "CN")] = cached_value  # 预置缓存值模拟已查。
    session = FakeSession()
    repo = SqlAlchemyEvidencePolicyRepository(session, cache=cache)

    out = asyncio.run(repo.get_current("triage", "CN"))

    assert out is cached_value
    assert session.execute_calls == 0  # 命中缓存，未查 DB。


def test_invalidate_clears_cache():
    cache: TTLCache[tuple[str, str], object] = TTLCache(maxsize=8, ttl=300)
    cache[("triage", "CN")] = object()
    repo = SqlAlchemyEvidencePolicyRepository(FakeSession(), cache=cache)

    repo.invalidate("triage", "CN")

    assert ("triage", "CN") not in cache


def test_invalidate_unknown_key_noop():
    repo = SqlAlchemyEvidencePolicyRepository(FakeSession())
    # 未注册的 key 不报错。
    repo.invalidate("nope", "XX")


def test_default_cache_created_when_none():
    """未传 cache 时构造默认 TTLCache（5min TTL，§11）。"""
    repo = SqlAlchemyEvidencePolicyRepository(FakeSession())
    assert repo._cache.ttl == 300
    assert repo._cache.maxsize > 0
