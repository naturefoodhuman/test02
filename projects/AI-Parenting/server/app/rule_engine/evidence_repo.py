# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/rule_engine/evidence_repo.py —— EvidencePolicy 仓储（APC-T018）。
# 依据：ENGINEERING_DESIGN §6.1（evidence_policy：policy_type+region+version UNIQUE，
#       effective_to IS NULL 当前生效）、§11（L1 缓存 TTLCache 5min，写入显式 invalidate，
#       医疗规则缓存写入时立即失效杜绝 stale rule）、§13.2（激活新版本旧版本 effective_to 自动关闭）；
#       ARCHITECTURE_FINAL §18（规则库强制递增 version，保留历史版本）；TASK_BACKLOG APC-T018。
# 设计：EvidencePolicyRepository Protocol + SqlAlchemyEvidencePolicyRepository。
#       - upsert(pack)：写入新版本（version 强制递增校验），effective_to=NULL 当前生效。
#       - activate(policy_type, region, version)：激活指定版本——旧生效版本 effective_to=now
#         自动关闭（§13.2），目标版本 effective_to 置 NULL；事务内完成。
#       - get_current(policy_type, region)：取当前生效版本（effective_to IS NULL），
#         L1 TTLCache 命中即返回；未命中查 DB 并回填。
#       - 写入/激活后 invalidate(policy_type, region)：清缓存，杜绝 stale rule（§11 铁律）。
#       - 不可软删除（保留历史版本用于审计追溯，§18）。
# 边界：只读写 evidence_policy 表；不做规则求值（求值在 kernel/RuleModule）；
#       缓存为进程内（家庭尺度并发极低，§11 禁止 Redis）。

"""EvidencePolicy 仓储（APC-T018）。

架构（ENGINEERING_DESIGN §6.1 / §11 / §13.2）：``evidence_policy`` 以
``(policy_type, region, version)`` UNIQUE，``effective_to IS NULL`` 标记当前生效版本。
规则库变更强制递增 ``version``（架构 §18），保留历史版本用于审计追溯（不可软删除）。

``EvidencePolicyRepository`` 协议 + ``SqlAlchemyEvidencePolicyRepository`` 实现：
    - ``upsert(pack)``：写入新版本（校验 version 严格递增），``effective_to=NULL`` 当前生效。
    - ``activate(policy_type, region, version)``：激活指定版本——旧生效版本
      ``effective_to=now`` 自动关闭（§13.2），目标版本 ``effective_to`` 置 NULL；事务内完成。
    - ``get_current(policy_type, region)``：取当前生效版本；L1 ``TTLCache`` 命中即返回。
    - 写入/激活后 ``invalidate(policy_type, region)``：清缓存，杜绝 stale rule（§11 铁律）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cachetools import TTLCache
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.clock import Clock, SystemClock
from ..common.ids import new_id
from ..models.rules import EvidencePolicy as EvidencePolicyOrm
from .domain.models import RulePack


@runtime_checkable
class EvidencePolicyRepository(Protocol):
    """EvidencePolicy 仓储协议（APC-T018）。"""

    async def upsert(self, pack: RulePack) -> EvidencePolicyOrm:
        """写入新版本规则包（version 严格递增校验），effective_to=NULL 当前生效。"""
        ...

    async def activate(self, policy_type: str, region: str, version: int) -> EvidencePolicyOrm:
        """激活指定版本：旧生效版本 effective_to=now 自动关闭，目标版本 effective_to 置 NULL。"""
        ...

    async def get_current(self, policy_type: str, region: str) -> EvidencePolicyOrm | None:
        """取当前生效版本（effective_to IS NULL）；L1 缓存命中即返回。"""
        ...

    def invalidate(self, policy_type: str, region: str) -> None:
        """清当前生效缓存（写入/激活后调用，杜绝 stale rule，§11 铁律）。"""
        ...


class SqlAlchemyEvidencePolicyRepository:
    """``EvidencePolicyRepository`` 的 SQLAlchemy 实现（APC-T018）。

    缓存：L1 进程内 ``TTLCache``（TTL 5min，§11），key=``(policy_type, region)``。
    写入/激活后 ``invalidate`` 清缓存——医疗规则缓存写入时立即失效，杜绝 stale rule。
    """

    def __init__(
        self,
        session: AsyncSession,
        clock: Clock | None = None,
        cache: TTLCache[tuple[str, str], EvidencePolicyOrm] | None = None,
    ) -> None:
        self._session = session
        self._clock = clock or SystemClock()
        # L1 缓存：TTL 5min（§11）；maxsize 充足（policy_type×region 组合有限）。
        self._cache: TTLCache[tuple[str, str], EvidencePolicyOrm] = cache or TTLCache(
            maxsize=256, ttl=300
        )

    async def upsert(self, pack: RulePack) -> EvidencePolicyOrm:
        """写入新版本规则包（version 严格递增校验），effective_to=NULL 当前生效。

        - 校验新 version 严格大于当前最大 version（强制递增，架构 §18）。
        - 旧生效版本 ``effective_to=now`` 自动关闭（新版本生效即旧版本失效，§13.2）。
        - 重复 ``(policy_type, region, version)`` 由 DB UNIQUE 约束兜底（IntegrityError）。
        - 写入后 ``invalidate`` 清缓存。
        """
        # 校验 version 严格递增：取当前最大 version。
        max_version = await self._max_version(pack.policy_type, pack.region)
        if max_version is not None and pack.version <= max_version:
            raise ValueError(
                f"evidence_policy {pack.policy_type}/{pack.region} version must strictly "
                f"increase: current_max={max_version} new={pack.version}"
            )
        now = self._clock.now()
        # 旧生效版本自动关闭（effective_to IS NULL → now）。
        await self._session.execute(
            update(EvidencePolicyOrm)
            .where(
                EvidencePolicyOrm.policy_type == pack.policy_type,
                EvidencePolicyOrm.region == pack.region,
                EvidencePolicyOrm.effective_to.is_(None),
            )
            .values(effective_to=now)
        )
        row = EvidencePolicyOrm(
            id=new_id(),
            policy_type=pack.policy_type,
            region=pack.region,
            version=pack.version,
            effective_from=pack.effective_from,
            effective_to=None,
            source=pack.source,
            rule_text=pack.rule_text,
            display_text=pack.display_text,
            hash=pack.hash or "",
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError(
                f"evidence_policy {pack.policy_type}/{pack.region}@v{pack.version} "
                f"already exists (UNIQUE constraint)"
            ) from exc
        self.invalidate(pack.policy_type, pack.region)
        return row

    async def activate(self, policy_type: str, region: str, version: int) -> EvidencePolicyOrm:
        """激活指定版本：旧生效版本 effective_to=now 自动关闭，目标版本 effective_to 置 NULL。

        事务内完成（旧关闭 + 目标激活原子）；目标版本不存在 → ValueError。
        激活后 ``invalidate`` 清缓存。
        """
        now = self._clock.now()
        # 旧生效版本自动关闭。
        await self._session.execute(
            update(EvidencePolicyOrm)
            .where(
                EvidencePolicyOrm.policy_type == policy_type,
                EvidencePolicyOrm.region == region,
                EvidencePolicyOrm.effective_to.is_(None),
            )
            .values(effective_to=now)
        )
        # 目标版本 effective_to 置 NULL（重新生效）。
        result = await self._session.execute(
            update(EvidencePolicyOrm)
            .where(
                EvidencePolicyOrm.policy_type == policy_type,
                EvidencePolicyOrm.region == region,
                EvidencePolicyOrm.version == version,
            )
            .values(effective_to=None)
            .returning(EvidencePolicyOrm)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"evidence_policy {policy_type}/{region}@v{version} not found")
        await self._session.flush()
        self.invalidate(policy_type, region)
        return row

    async def get_current(self, policy_type: str, region: str) -> EvidencePolicyOrm | None:
        """取当前生效版本（effective_to IS NULL）；L1 缓存命中即返回。"""
        key = (policy_type, region)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        stmt = select(EvidencePolicyOrm).where(
            EvidencePolicyOrm.policy_type == policy_type,
            EvidencePolicyOrm.region == region,
            EvidencePolicyOrm.effective_to.is_(None),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            self._cache[key] = row
        return row

    def invalidate(self, policy_type: str, region: str) -> None:
        """清当前生效缓存（写入/激活后调用，杜绝 stale rule，§11 铁律）。"""
        self._cache.pop((policy_type, region), None)

    async def _max_version(self, policy_type: str, region: str) -> int | None:
        """取 (policy_type, region) 当前最大 version（无记录返回 None）。"""
        stmt = select(func.max(EvidencePolicyOrm.version)).where(
            EvidencePolicyOrm.policy_type == policy_type,
            EvidencePolicyOrm.region == region,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()


__all__ = ["EvidencePolicyRepository", "SqlAlchemyEvidencePolicyRepository"]
