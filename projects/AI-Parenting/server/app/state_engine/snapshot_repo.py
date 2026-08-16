# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/snapshot_repo.py —— derived_baby_state 快照仓储（APC-T016）。
# 依据：ENGINEERING_DESIGN §6.1（derived_baby_state：baby_id PK + snapshot jsonb + computed_at）、
#       §6.3（snapshot 含 computed_at 与 source event range）、§7.1；
#       ARCHITECTURE_FINAL §6.1、§10.1；TASK_BACKLOG APC-T016。
# 设计：SnapshotRepository Protocol + SqlAlchemySnapshotRepository。
#       upsert：baby_id 为 PK，INSERT ... ON CONFLICT (baby_id) DO UPDATE（单行 per baby，§6.1）。
#       get：反序列化 snapshot jsonb → DerivedBabyState（含 computed_at + source_event_range）。
# 边界：只读写 derived_baby_state 表，不读事件（事件加载在 engine）；不产生告警。

"""derived_baby_state 快照仓储（APC-T016）。

架构（ENGINEERING_DESIGN §6.1 / §6.3）：``derived_baby_state`` 以 ``baby_id`` 为 PK，
单行 per baby，每次派生 upsert 覆盖当前快照。``snapshot`` jsonb 含各域指标 +
``computed_at`` + ``source_event_range``（§6.3）。

``SnapshotRepository`` 协议 + ``SqlAlchemySnapshotRepository`` 实现：
    - ``upsert(baby_id, state)``：写入/覆盖快照（ON CONFLICT (baby_id) DO UPDATE）。
    - ``get(baby_id)``：读取并反序列化为 ``DerivedBabyState``；无记录返回 None。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.derived import DerivedBabyState as DerivedBabyStateOrm
from .domain import (
    DerivedBabyState,
    DiaperProjection,
    FeedingProjection,
    SleepProjection,
    SupplementProjection,
    TemperatureProjection,
)


@runtime_checkable
class SnapshotRepository(Protocol):
    """派生状态快照仓储协议（APC-T016）。"""

    async def upsert(self, baby_id: str, state: DerivedBabyState) -> None:
        """写入/覆盖 baby 的派生快照（幂等 upsert，baby_id PK）。"""
        ...

    async def get(self, baby_id: str) -> DerivedBabyState | None:
        """读取 baby 最新派生快照；无记录返回 None。"""
        ...


class SqlAlchemySnapshotRepository:
    """``SnapshotRepository`` 的 SQLAlchemy 实现（APC-T016）。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, baby_id: str, state: DerivedBabyState) -> None:
        snapshot = state.to_snapshot()
        stmt = pg_insert(DerivedBabyStateOrm).values(
            baby_id=baby_id,
            snapshot=snapshot,
            computed_at=state.computed_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["baby_id"],
            set_={"snapshot": snapshot, "computed_at": state.computed_at},
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get(self, baby_id: str) -> DerivedBabyState | None:
        stmt = select(DerivedBabyStateOrm).where(DerivedBabyStateOrm.baby_id == baby_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return _from_snapshot(row.snapshot, row.computed_at)


def _from_snapshot(snapshot: dict, computed_at) -> DerivedBabyState:
    """反序列化 snapshot jsonb → DerivedBabyState（T016 读取用）。

    snapshot 结构与 ``DerivedBabyState.to_snapshot()`` 对称（§6.3）。
    """
    feeding = snapshot.get("feeding", {})
    diaper = snapshot.get("diaper", {})
    sleep = snapshot.get("sleep", {})
    temperature = snapshot.get("temperature", {})
    supplement = snapshot.get("supplement", {})
    rng = snapshot.get("source_event_range", [None, None])

    current_session = sleep.get("current_session_started_at")
    current_session_dt = None
    if current_session is not None:
        from datetime import datetime
        current_session_dt = datetime.fromisoformat(current_session)

    range_start = None
    range_end = None
    if isinstance(rng, list) and len(rng) == 2:
        from datetime import datetime
        if rng[0] is not None:
            range_start = datetime.fromisoformat(rng[0])
        if rng[1] is not None:
            range_end = datetime.fromisoformat(rng[1])

    return DerivedBabyState(
        feeding=FeedingProjection(
            last_feeding_ago_seconds=feeding.get("last_feeding_ago_seconds"),
            volume_ml_24h=feeding.get("volume_ml_24h", 0.0),
            count_24h=feeding.get("count_24h", 0),
        ),
        diaper=DiaperProjection(
            wet_count_24h=diaper.get("wet_count_24h", 0),
            dirty_count_24h=diaper.get("dirty_count_24h", 0),
        ),
        sleep=SleepProjection(
            total_seconds_24h=sleep.get("total_seconds_24h", 0.0),
            current_session_started_at=current_session_dt,
        ),
        temperature=TemperatureProjection(max_c_24h=temperature.get("max_c_24h")),
        supplement=SupplementProjection(
            last_supplement_ago_seconds=supplement.get("last_supplement_ago_seconds"),
            last_supplement_name=supplement.get("last_supplement_name"),
        ),
        computed_at=computed_at,
        source_event_range=(range_start, range_end),
    )


__all__ = ["SnapshotRepository", "SqlAlchemySnapshotRepository"]
