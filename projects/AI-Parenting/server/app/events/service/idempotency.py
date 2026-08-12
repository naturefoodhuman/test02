# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/service/idempotency.py —— 事件幂等写入用例服务。
# 依据：ENGINEERING_DESIGN §5.1（ObservationEvent 契约）、§5.2（事务边界在 service）、
#       §9.1（异常）、§10.4（Audit 不可绕过，mutating 留痕）、§6.2（双状态字段）；
#       ARCHITECTURE_FINAL §6.2/§6.3（统一事件模型 + 同步契约）、§5.1（correction 链）、§505（幂等）；
#       TASK_BACKLOG APC-T009（重复 event_id 不创建重复记录；correction_of 与 is_deleted 保留）。
# 设计：用例层，依赖注入 ObservationEventRepository / Clock（架构 §5：Protocol+DI）。
#       事务边界在本层：mutating 方法 flush 后由本服务 commit（若有 session）。
#       幂等（架构 §505）：record() 以 event_id 为幂等键，重复提交返回既有 event_id，不创建重复行。
#       纠错（架构 §5.1 correction 链）：correct() 软删除旧事件 + 新事件 correction_of 指向旧 event_id。
#       审计（§10.4）：mutating 方法接可选 audit: AuditService | None；提供则 append，不提供则跳过
#       （T009 无 API 层；T010 gateway 注入 AuditService 启用留痕）。
# 边界：不感知 HTTP；不直接访问 DB（委托 Repository）；event_id 应用层生成（ULID）。

"""事件幂等写入用例服务（record / correct / soft_delete）。

架构（ENGINEERING_DESIGN §5.2）：用例层依赖注入 Protocol 实现，测试可注入替身。
本服务编排 ``ObservationEventRepository`` / ``Clock``，事务边界在本层
（mutating 方法 flush 后 commit，若有 session）。

幂等（架构 §505 / APC-T009）：``record`` 以 ``event_id`` 为幂等键——
重复提交同一 event_id 返回既有记录，不创建重复行、不抛 ConflictError。
event_id 由调用方提供（客户端生成 ULID，断网记录成功即视为记录成功，架构铁律 8），
服务端据此去重。

纠错（架构 §5.1 correction 链）：``correct`` 软删除旧事件 + 新事件 ``correction_of``
指向旧 event_id，不物理删除（§5.1）。

审计（§10.4）：mutating 方法接可选 ``audit: AuditService | None``；提供则 ``append``
留痕，不提供则跳过。T009 无 API 层，T010 gateway 注入 AuditService 启用留痕。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...common.clock import Clock
from ...common.errors import NotFoundError, ValidationError
from ...common.ids import is_valid_ulid, new_id
from ...observability.audit import AuditService
from ..domain import (
    ObservationEvent,
    ObservationEventRepository,
    ProcessingStatus,
    Source,
    SyncStatus,
)


class EventService:
    """事件用例服务（幂等写入 / 纠错 / 软删除）。

    生命周期：请求作用域（依赖 ``ObservationEventRepository`` 持有请求级 ``AsyncSession``）。
    ``session`` 可选（mutating 方法成功后 commit；Fake 替身测试不传则跳过 commit）。
    事务边界在 service 层（架构 §5.2）：mutating 方法 flush 后由本服务 commit。
    """

    def __init__(
        self,
        *,
        repository: ObservationEventRepository,
        clock: Clock,
        session: AsyncSession | None = None,
    ) -> None:
        self._repo = repository
        self._clock = clock
        self._session = session

    async def _commit(self) -> None:
        """提交事务（若有 session）；Fake 替身测试无 session 时跳过。"""
        if self._session is not None:
            await self._session.commit()

    async def record(
        self,
        *,
        event_id: str,
        baby_id: str,
        family_id: str,
        event_type: str,
        start_time: datetime,
        client_created_at: datetime,
        normalized_payload: dict[str, Any],
        source: Source,
        user_id: str | None = None,
        device_id: str | None = None,
        end_time: datetime | None = None,
        raw_input: dict[str, Any] | None = None,
        confidence: float = 1.0,
        attachments: list[str] | None = None,
        sync_status: SyncStatus = SyncStatus.PENDING,
        processing_status: ProcessingStatus = ProcessingStatus.PENDING,
        audit: AuditService | None = None,
    ) -> ObservationEvent:
        """幂等写入一条 ObservationEvent，返回事件领域模型。

        幂等（架构 §505 / APC-T009）：``event_id`` 已存在则返回既有记录，不创建重复行。
        ``event_id`` 由调用方提供（客户端生成 ULID），服务端据此去重——客户端重试/
        网络重传同一 event_id 不会产生重复事件（架构铁律 8：离线记录不得丢失）。

        ``server_received_at`` 由本服务用注入的 ``Clock`` 填充（服务端权威接收时间，
        同步契约字段，架构 §6.3），不接受调用方覆盖。

        校验：``event_id`` / ``baby_id`` / ``family_id`` 须为合法 ULID；
        ``confidence`` 须在 [0,1]；``source`` 须为合法枚举（Pydantic 已校验）。
        """
        if not is_valid_ulid(event_id):
            raise ValidationError("Invalid event_id", evidence={"event_id": event_id})
        if not is_valid_ulid(baby_id):
            raise ValidationError("Invalid baby_id", evidence={"baby_id": baby_id})
        if not is_valid_ulid(family_id):
            raise ValidationError("Invalid family_id", evidence={"family_id": family_id})

        event = ObservationEvent(
            event_id=event_id,
            baby_id=baby_id,
            family_id=family_id,
            user_id=user_id,
            device_id=device_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            client_created_at=client_created_at,
            server_received_at=self._clock.now(),
            raw_input=raw_input,
            normalized_payload=normalized_payload,
            confidence=confidence,
            source=source,
            attachments=attachments or [],
            correction_of=None,
            is_deleted=False,
            sync_status=sync_status,
            processing_status=processing_status,
        )
        result = await self._repo.upsert(event)
        if audit is not None:
            await audit.append(
                actor=_current_actor(),
                action="create",
                resource=f"observation_event/{result.event_id}",
                after={
                    "baby_id": baby_id,
                    "event_type": event_type,
                    "source": source.value,
                    "sync_status": result.sync_status.value,
                    "processing_status": result.processing_status.value,
                },
            )
        await self._commit()
        return result

    async def correct(
        self,
        *,
        correction_of: str,
        baby_id: str,
        family_id: str,
        event_type: str,
        start_time: datetime,
        client_created_at: datetime,
        normalized_payload: dict[str, Any],
        source: Source,
        user_id: str | None = None,
        device_id: str | None = None,
        end_time: datetime | None = None,
        raw_input: dict[str, Any] | None = None,
        confidence: float = 1.0,
        attachments: list[str] | None = None,
        audit: AuditService | None = None,
    ) -> ObservationEvent:
        """纠正一条事件（correction 链，架构 §5.1）。

        流程：
            1. 校验被纠正事件存在（未删除）；不存在 → ``NotFoundError``。
            2. 软删除旧事件（``is_deleted=true``，不物理删除，§5.1）。
            3. 新建事件，``correction_of`` 指向旧 event_id（新 event_id 由本服务生成）。

        返回新建的纠正事件。纠错链可链式（纠正的纠正），``correction_of`` 始终指向
        直接被纠正的事件（不做传递归一化，便于审计追溯）。
        """
        if not is_valid_ulid(correction_of):
            raise ValidationError(
                "Invalid correction_of", evidence={"correction_of": correction_of}
            )
        original = await self._repo.get(correction_of)
        if original is None:
            raise NotFoundError("Original event not found", evidence={"event_id": correction_of})

        # 软删除旧事件（不物理删除，§5.1）。
        await self._repo.soft_delete(correction_of)

        new_event = ObservationEvent(
            event_id=new_id(),
            baby_id=baby_id,
            family_id=family_id,
            user_id=user_id,
            device_id=device_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            client_created_at=client_created_at,
            server_received_at=self._clock.now(),
            raw_input=raw_input,
            normalized_payload=normalized_payload,
            confidence=confidence,
            source=source,
            attachments=attachments or [],
            correction_of=correction_of,
            is_deleted=False,
            sync_status=SyncStatus.PENDING,
            processing_status=ProcessingStatus.PENDING,
        )
        result = await self._repo.upsert(new_event)
        if audit is not None:
            await audit.append(
                actor=_current_actor(),
                action="correct",
                resource=f"observation_event/{result.event_id}",
                after={
                    "correction_of": correction_of,
                    "baby_id": baby_id,
                    "event_type": event_type,
                    "source": source.value,
                },
            )
        await self._commit()
        return result

    async def soft_delete(
        self,
        *,
        event_id: str,
        audit: AuditService | None = None,
    ) -> ObservationEvent:
        """软删除一条事件（置 is_deleted=true，不物理删除，§5.1）。

        不存在或已删除 → ``NotFoundError``。
        """
        deleted = await self._repo.soft_delete(event_id)
        if deleted is None:
            raise NotFoundError("Event not found", evidence={"event_id": event_id})
        if audit is not None:
            await audit.append(
                actor=_current_actor(),
                action="delete",
                resource=f"observation_event/{event_id}",
                after={"is_deleted": True},
            )
        await self._commit()
        return deleted

    async def list_events(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ObservationEvent]:
        """查询事件时间线（按 start_time DESC，§6.1 索引；默认排除软删除，§5.1）。

        供 API 层（GET /events）与 Timeline 复用（TASK_BACKLOG APC-T010 DoD）。
        """
        return await self._repo.query(
            baby_id=baby_id,
            family_id=family_id,
            event_type=event_type,
            limit=limit,
        )


def _current_actor() -> str:
    """从 logger contextvars 取当前操作人（user_id/device_id/system）。

    与 ``@audit`` 装饰器一致（§10.4）：无上下文则 ``system``。
    """
    from ...observability.logger import get_context  # 延迟导入避免循环依赖

    ctx = get_context()
    return ctx.get("user_id") or ctx.get("device_id") or "system"


__all__ = ["EventService"]
