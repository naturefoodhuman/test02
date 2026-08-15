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

from sqlalchemy import select
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


__all__ = ["SqlAlchemyLogWriter"]
