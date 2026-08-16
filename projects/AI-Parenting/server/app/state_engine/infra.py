# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/infra.py —— State Engine 基础设施实现（APC-T016）。
# 依据：ENGINEERING_DESIGN §6.2、§7.1；TASK_BACKLOG APC-T016。
# 设计：SqlAlchemyEventLoader 按 baby_id 加载所有未删除事件（按 start_time 升序），
#       供 StateEngine.recompute 全量重算。不依赖 query 的 limit 语义（明确"全部"）。
# 边界：只读事件，不写；软删除过滤（架构 §5.1）。

"""State Engine 基础设施实现（APC-T016）。

``SqlAlchemyEventLoader``：按 ``baby_id`` 加载所有未删除 ``observation_event`` 行
（按 ``start_time`` 升序），供 ``StateEngine.recompute`` 全量重算。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..events.domain import ObservationEvent
from ..models.events import ObservationEvent as Orm


class SqlAlchemyEventLoader:
    """按 baby 加载未删除事件的 SQLAlchemy 实现（APC-T016）。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_by_baby(self, baby_id: str) -> list[ObservationEvent]:
        stmt = (
            select(Orm)
            .where(Orm.baby_id == baby_id, Orm.is_deleted.is_(False))
            .order_by(Orm.start_time.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        # ORM → 领域模型：复用 events infra repository 的模块级转换函数。
        from ..events.infra.repository import _from_orm

        return [_from_orm(row) for row in rows]


__all__ = ["SqlAlchemyEventLoader"]
