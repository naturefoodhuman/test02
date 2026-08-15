# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
#
# app/normalization/infra/log_writer.py —— 派生表写入仓储（APC-T013）。
# 依据：ENGINEERING_DESIGN §6.1（各 *_log 含 event_id FK 溯源）、§7.1；
#       TASK_BACKLOG APC-T013。
# 设计：SqlAlchemyLogWriter 按 NormalizedRecord.table 构造对应 ORM（feeding_log 有结构化列，
#       其余 log 用 _LogBase 共享列 event_id/baby_id/payload），写入 PG。
#       幂等：exists() 按 event_id 查表去重（与 NormalizationService 配合）。
# 边界：只写派生表，不更新 observation_event（processing_status 由 EventRepository 推进）。

"""派生表写入仓储（APC-T013）。

``SqlAlchemyLogWriter`` 按 ``NormalizedRecord.table`` 构造对应 ORM：
    - ``feeding_log``：结构化列（amount_ml/feeding_type/started_at/ended_at）+ payload jsonb。
    - 其余 log（diaper/sleep/temperature/supplement）：``_LogBase`` 共享列
      （event_id/baby_id/payload jsonb），无额外结构化列。

幂等：``exists()`` 按 ``event_id`` 查表去重（与 ``NormalizationService`` 配合）。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...common.ids import new_id
from ...models.logs import (
    DiaperLog,
    FeedingLog,
    SleepLog,
    SupplementLog,
    TemperatureLog,
)
from ..domain import NormalizedRecord

# table 名 → ORM 类映射（type[Any]：各 log 类共享 _LogBase.event_id，但 mypy
# 无法从 Base 推断 _LogBase 列，故用 Any 放宽；运行时各 ORM 均含 event_id/baby_id/payload）。
_TABLE_TO_ORM: dict[str, type[Any]] = {
    "feeding_log": FeedingLog,
    "diaper_log": DiaperLog,
    "sleep_log": SleepLog,
    "temperature_log": TemperatureLog,
    "supplement_log": SupplementLog,
}


class SqlAlchemyLogWriter:
    """派生表写入仓储（APC-T013）。

    生命周期：请求作用域（与 ``NormalizationService`` 共享 ``AsyncSession``）。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, event_id: str, table: str) -> bool:
        """``event_id`` 是否已在 ``table`` 派生表存在（幂等去重）。"""
        orm_cls = _TABLE_TO_ORM.get(table)
        if orm_cls is None:
            return False
        stmt = select(orm_cls.id).where(orm_cls.event_id == event_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def write(self, record: NormalizedRecord) -> None:
        """写 ``NormalizedRecord`` 到对应 ``*_log`` 表。

        调用方应先 ``exists()`` 去重；本方法不做重复检查（service 层负责幂等）。
        """
        orm_cls = _TABLE_TO_ORM.get(record.table)
        if orm_cls is None:
            raise ValueError(f"Unknown log table: {record.table}")

        row: Any
        if record.table == "feeding_log":
            row = FeedingLog(
                id=new_id(),
                event_id=record.event_id,
                baby_id=record.baby_id,
                payload=record.payload,
                amount_ml=record.structured.get("amount_ml"),
                feeding_type=record.structured.get("feeding_type"),
                started_at=record.structured["started_at"],
                ended_at=record.structured.get("ended_at"),
            )
        else:
            # 其余 log：_LogBase 共享列（event_id/baby_id/payload）。
            row = orm_cls(
                id=new_id(),
                event_id=record.event_id,
                baby_id=record.baby_id,
                payload=record.payload,
            )
        self._session.add(row)
        await self._session.flush()

    async def soft_delete_by_event(self, event_id: str, table: str) -> int:
        """置 ``table`` 中 ``event_id`` 对应派生行 ``is_deleted=true``（APC-T014）。

        供纠错链（``correction_of`` 触发旧派生行失效）与事件软删除（派生表排除）。
        架构 §5.1 不物理删除——派生表行只置 ``is_deleted``，State Engine 重算时排除。
        返回受影响行数（0 表示无对应派生行）。
        """
        orm_cls = _TABLE_TO_ORM.get(table)
        if orm_cls is None:
            return 0
        stmt = (
            update(orm_cls)
            .where(
                orm_cls.event_id == event_id,
                orm_cls.is_deleted.is_(False),
            )
            .values(is_deleted=True)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        # asyncpg 的 CursorResult 有 rowcount，但 mypy 的 Result 协议未声明；安全取值。
        return int(getattr(result, "rowcount", 0) or 0)


__all__ = ["SqlAlchemyLogWriter"]
