# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""EvidencePolicy 仓储集成测试（APC-T018，需 DB）。

覆盖 DB 持久化：upsert（version 递增校验 + 旧版本自动关闭）、activate（旧版本关闭 +
目标版本生效）、get_current（effective_to IS NULL 查询 + 缓存）、写入后缓存失效。
连 AI_parenting_dev 库。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select

from server.app import db as db_module
from server.app.common.clock import FixedClock
from server.app.db import get_session_factory
from server.app.models.rules import EvidencePolicy as Orm
from server.app.rule_engine.domain.models import Rule, RuleAction, RuleCondition, RulePack
from server.app.rule_engine.evidence_repo import SqlAlchemyEvidencePolicyRepository
from server.app.settings import get_settings

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 16, 0, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_db():
    """重置 engine 单例（与 test_state_engine 同模式）。

    evidence_policy 表清理在每个测试的 ``run()`` 开头做（共用同一 asyncio.run 循环，
    避免 fixture 里 asyncio.run 导致 engine 绑死循环）。
    """
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _cleanup(session) -> None:
    """清空 evidence_policy（version 递增校验要求测试间无残留）。"""
    await session.execute(delete(Orm))
    await session.commit()


def _pack(version: int, *, policy_type: str = "triage", region: str = "CN") -> RulePack:
    return RulePack(
        policy_type=policy_type,
        region=region,
        version=version,
        effective_from=NOW,
        source="test",
        rule_text="r",
        display_text="d",
        rules=[
            Rule(
                rule_id="r1",
                conditions=[RuleCondition(op="lt", field="baby_age_days", value=90)],
                action=RuleAction(verdict="warn", outputs={}, reason_code="r1", evidence_text="e"),
            )
        ],
    )


def _run(coro):
    return asyncio.run(coro)


def test_upsert_writes_new_version_and_closes_old():
    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as _s:
            await _cleanup(_s)
        # v1
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            row1 = await repo.upsert(_pack(1))
            await s.commit()
            assert row1.version == 1
            assert row1.effective_to is None  # 当前生效。
        # v2
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            row2 = await repo.upsert(_pack(2))
            await s.commit()
            assert row2.version == 2
            assert row2.effective_to is None
        # v1 应已自动关闭。
        async with factory() as s:
            r1 = (
                await s.execute(
                    select(Orm).where(
                        Orm.policy_type == "triage",
                        Orm.region == "CN",
                        Orm.version == 1,
                    )
                )
            ).scalar_one()
            assert r1.effective_to == NOW

    _run(run())


def test_upsert_rejects_non_increasing_version():
    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as _s:
            await _cleanup(_s)
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            await repo.upsert(_pack(1))
            await s.commit()
        # 再写 v1（不递增）→ 拒绝。
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            with pytest.raises(ValueError, match="must strictly increase"):
                await repo.upsert(_pack(1))

    _run(run())


def test_get_current_returns_effective_version_and_caches():
    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as _s:
            await _cleanup(_s)
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            await repo.upsert(_pack(1))
            await repo.upsert(_pack(2))
            await s.commit()
        # 当前生效应为 v2。
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            cur = await repo.get_current("triage", "CN")
            assert cur is not None
            assert cur.version == 2
            # 第二次命中缓存（不查 DB）。
            cur2 = await repo.get_current("triage", "CN")
            assert cur2 is cur

    _run(run())


def test_activate_reopens_old_version_and_closes_current():
    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as _s:
            await _cleanup(_s)
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            await repo.upsert(_pack(1))
            await repo.upsert(_pack(2))
            await s.commit()
        # 激活回 v1：v2 关闭，v1 重新生效。
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            row = await repo.activate("triage", "CN", 1)
            await s.commit()
            assert row.version == 1
            assert row.effective_to is None
        async with factory() as s:
            v2 = (
                await s.execute(
                    select(Orm).where(
                        Orm.policy_type == "triage",
                        Orm.region == "CN",
                        Orm.version == 2,
                    )
                )
            ).scalar_one()
            assert v2.effective_to == NOW  # v2 已关闭。
            cur = await SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW)).get_current(
                "triage", "CN"
            )
            assert cur is not None
            assert cur.version == 1  # 当前生效回到 v1。

    _run(run())


def test_activate_unknown_version_raises():
    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as _s:
            await _cleanup(_s)
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            with pytest.raises(ValueError, match="not found"):
                await repo.activate("triage", "CN", 99)

    _run(run())


def test_invalidate_after_upsert_forces_db_requery():
    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as _s:
            await _cleanup(_s)
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            await repo.upsert(_pack(1))
            await s.commit()
            cur = await repo.get_current("triage", "CN")
            assert cur is not None and cur.version == 1
        # 新 session 新 repo：upsert v2 后缓存应失效，get_current 返回 v2。
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            await repo.upsert(_pack(2))
            await s.commit()
            cur = await repo.get_current("triage", "CN")
            assert cur is not None and cur.version == 2

    _run(run())
