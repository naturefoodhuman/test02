# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/infra/repository.py —— ObservationEvent 仓储实现（事件溯源核心）。
# 依据：ENGINEERING_DESIGN §5.1（ObservationEvent 数据契约 SSOT）、§5.2（Repository Protocol）、
#       §6.1/§6.2（observation_event 表 + 双状态字段）；ARCHITECTURE_FINAL §6.2/§6.3/§5.1；
#       TASK_BACKLOG APC-T009（重复 event_id 不创建重复记录；correction_of 与 is_deleted 保留）。
# 设计：基于 AsyncSession 的请求作用域仓储（架构 §5.2：生命周期请求作用域，事务边界在 service）。
#       幂等 upsert（架构 §505）：先按 event_id 查，已存在则返回既有记录（不创建重复行），
#       不存在则插入新记录。event_id 为应用层生成 ULID（幂等键）。
#       软删除过滤：查询默认排除 is_deleted（架构 §5.1：不物理删除）。
#       Pydantic 契约 ↔ ORM 互转：to_orm / from_orm 集中在本层，上层只认领域模型。
# 边界：只做数据访问，不含业务规则（幂等策略/审计在 service）；异常由 service 层映射。
#       flush 不 commit（事务边界在 service）。

"""ObservationEvent 仓储实现（事件溯源核心，幂等 upsert）。

架构（ENGINEERING_DESIGN §5.2）：``Repository`` 请求作用域，事务边界在 service 层。
本模块实现 ``domain.ObservationEventRepository`` 协议，基于 ``AsyncSession``，
仅做数据访问；业务规则（幂等策略、审计）在 ``events.service``。

表结构 SSOT：``ENGINEERING_DESIGN §6.1`` + ``§5.1`` ——
- ``observation_event``：见 §5.1；PK event_id（ULID）；idx(baby_id,event_type,start_time DESC)；
  双状态字段 sync_status(pending|synced) + processing_status(pending|normalized|projected)；
  correction_of 自引用；is_deleted 软删除。

幂等（架构 §505 / APC-T009）：``upsert`` 以 ``event_id`` 为幂等键，重复提交返回既有记录，
不创建重复行、不抛 ConflictError。event_id 由应用层生成（ULID），客户端重试/网络重传
同一 event_id 不会产生重复事件。

软删除：查询默认 ``is_deleted = false``（架构 §5.1：不物理删除，配合 partial index）。
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.events import ObservationEvent as ObservationEventOrm
from ..domain import (
    ObservationEvent,
    ProcessingStatus,
    Source,
    SyncStatus,
)


def _to_orm(entity: ObservationEvent) -> ObservationEventOrm:
    """Pydantic 领域模型 → ORM 实例（新建行用，不读既有）。"""
    return ObservationEventOrm(
        id=entity.event_id,
        baby_id=entity.baby_id,
        family_id=entity.family_id,
        user_id=entity.user_id,
        device_id=entity.device_id,
        event_type=entity.event_type,
        start_time=entity.start_time,
        end_time=entity.end_time,
        client_created_at=entity.client_created_at,
        server_received_at=entity.server_received_at,
        raw_input=entity.raw_input,
        normalized_payload=entity.normalized_payload,
        confidence=entity.confidence,
        source=entity.source.value,
        attachments=list(entity.attachments),
        correction_of=entity.correction_of,
        is_deleted=entity.is_deleted,
        sync_status=entity.sync_status.value,
        processing_status=entity.processing_status.value,
    )


def _from_orm(row: ObservationEventOrm) -> ObservationEvent:
    """ORM 实例 → Pydantic 领域模型（只读转换，不持久化）。"""
    return ObservationEvent(
        event_id=row.id,
        baby_id=row.baby_id,
        family_id=row.family_id,
        user_id=row.user_id,
        device_id=row.device_id,
        event_type=row.event_type,
        start_time=row.start_time,
        end_time=row.end_time,
        client_created_at=row.client_created_at,
        server_received_at=row.server_received_at,
        raw_input=row.raw_input,
        normalized_payload=row.normalized_payload,
        confidence=row.confidence,
        source=Source(row.source),
        attachments=list(row.attachments or []),
        correction_of=row.correction_of,
        is_deleted=row.is_deleted,
        sync_status=SyncStatus(row.sync_status),
        processing_status=ProcessingStatus(row.processing_status),
    )


class SqlAlchemyObservationEventRepository:
    """基于 ``AsyncSession`` 的 ObservationEvent 仓储（实现 domain.ObservationEventRepository）。

    生命周期：请求作用域（FastAPI ``Depends`` 注入 session）；事务边界在 service 层
    （service 决定 commit/rollback）。本仓储只 execute/flush，不 commit。

    幂等（架构 §505 / APC-T009）：``upsert`` 先按 event_id 查，已存在则返回既有记录，
    不创建重复行。event_id 为应用层生成 ULID（幂等键）。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: str) -> ObservationEvent | None:
        """按 event_id 取未删除事件（软删除过滤，§5.1）。"""
        stmt = select(ObservationEventOrm).where(
            ObservationEventOrm.id == event_id,
            ObservationEventOrm.is_deleted.is_(False),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _from_orm(row) if row is not None else None

    async def upsert(self, entity: ObservationEvent) -> ObservationEvent:
        """幂等写入：event_id 已存在则返回既有记录，否则插入新记录。

        幂等语义（架构 §505 / APC-T009）：重复提交合并，不创建重复 event_id 行，
        不抛 ConflictError。客户端重试/网络重传同一 event_id 不会产生重复事件。

        注：本方法不更新既有记录内容（幂等返回既有）；纠错走 correction_of 新建事件 +
        soft_delete 旧事件（架构 §5.1 correction 链），而非原地覆盖。
        """
        existing = await self._session.get(ObservationEventOrm, entity.event_id)
        if existing is not None:
            # 幂等：返回既有记录（含 is_deleted 的也返回，供调用方判断）。
            return _from_orm(existing)

        row = _to_orm(entity)
        self._session.add(row)
        await self._session.flush()
        return _from_orm(row)

    async def query(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ObservationEvent]:
        """按过滤条件查询未删除事件（按 start_time DESC，§6.1 索引）。"""
        stmt = select(ObservationEventOrm).where(ObservationEventOrm.is_deleted.is_(False))
        if baby_id is not None:
            stmt = stmt.where(ObservationEventOrm.baby_id == baby_id)
        if family_id is not None:
            stmt = stmt.where(ObservationEventOrm.family_id == family_id)
        if event_type is not None:
            stmt = stmt.where(ObservationEventOrm.event_type == event_type)
        stmt = stmt.order_by(ObservationEventOrm.start_time.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [_from_orm(r) for r in result.scalars().all()]

    async def soft_delete(self, event_id: str) -> ObservationEvent | None:
        """软删除事件（置 is_deleted=true，不物理删除，§5.1）。

        返回更新后的事件；不存在或已删除则返回 None。
        """
        stmt = (
            update(ObservationEventOrm)
            .where(
                ObservationEventOrm.id == event_id,
                ObservationEventOrm.is_deleted.is_(False),
            )
            .values(is_deleted=True)
            .returning(ObservationEventOrm)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        await self._session.flush()
        return _from_orm(row)

    async def update_processing_status(
        self, event_id: str, status: ProcessingStatus
    ) -> ObservationEvent | None:
        """推进 ``processing_status``（架构 §6.2 双状态机，APC-T013/T015）。

        与 ``sync_status`` 独立：只更新 ``processing_status``，不动 ``sync_status``。
        返回更新后的事件；不存在或已删除则返回 None。
        """
        stmt = (
            update(ObservationEventOrm)
            .where(
                ObservationEventOrm.id == event_id,
                ObservationEventOrm.is_deleted.is_(False),
            )
            .values(processing_status=status.value)
            .returning(ObservationEventOrm)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        await self._session.flush()
        return _from_orm(row)


__all__ = ["SqlAlchemyObservationEventRepository"]
