# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""Repository Protocol 单元测试。"""

from __future__ import annotations

from server.app.common.repository import Repository


class _FakeRepo:
    async def get(self, id_: str):
        return None

    async def upsert(self, entity):
        return entity

    async def query(self, **filters):
        return []


def test_fake_repo_satisfies_protocol():
    """runtime_checkable Protocol 可用 isinstance 校验。"""
    assert isinstance(_FakeRepo(), Repository)
