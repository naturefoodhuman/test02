# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-15 00:00:00
#
# app/normalization/worker.py —— Normalization 常驻 worker（APC-T014）。
# 依据：ENGINEERING_DESIGN §7.1（NOTIFY events.changed --> Normalization worker）、
#       §11（at-least-once + 幂等消费，崩溃恢复用 processing_status）、§6.2（双状态机）、
#       §5.1（correction 链 + 软删除不物理删除）；
#       ARCHITECTURE_FINAL §4.1、§5.1、§730；
#       TASK_BACKLOG APC-T014（Worker 消费 events.changed；重复消息不重复写派生表；
#       correction_of 触发旧派生记录失效；soft delete 触发派生表排除；
#       processing_status 可从 pending 推进到 normalized；崩溃恢复扫描 pending 可补处理）。
# 设计：NormalizationWorker 是一个 EventHandler（符合 common.event_bus.EventHandler 协议），
#       由 EventWorker.add_handler 注入。每条 events.changed payload（含 event_id/op）：
#         - insert/update/recover：加载事件 → 去重（processing_status 已 normalized/projected 跳过）
#           → 纠错链（correction_of 非空先软删除旧 event_id 派生行）→ normalize（写派生表 + 推进状态）。
#         - delete：软删除该 event_id 在所有 P0 派生表的行（派生表排除）。
#       事务边界：每条消息独立 session，handler 内 commit（与 EventService 一致，架构 §5.2）。
#       异常隔离：单条失败记日志不抛，避免阻断 EventBus 消费循环（at-least-once，靠 processing_status 补偿）。
# 边界：不做医疗判断；不产生告警；只消费 events.changed，不发布事件。

"""Normalization 常驻 worker（APC-T014）。

架构（ENGINEERING_DESIGN §7.1 / §11 / §5.1）：
``NormalizationWorker`` 是 ``EventWorker`` 的 handler，消费 ``events.changed`` NOTIFY
（payload 含 ``event_id`` / ``op``），按 ``op`` 分发：

    - ``insert`` / ``update`` / ``recover``：加载 ``ObservationEvent`` → 去重
      （``processing_status`` 已 ``normalized``/``projected`` 则跳过，避免重复 NOTIFY 重复处理）
      → 纠错链（``correction_of`` 非空时先软删除旧 ``event_id`` 在所有 P0 派生表的行）
      → ``NormalizationService.normalize``（写派生表 + 推进 ``processing_status=normalized``）。
    - ``delete``：软删除该 ``event_id`` 在所有 P0 派生表的行（派生表排除，§5.1 不物理删除）。

去重（APC-T014）双层：
    1. worker 层：``processing_status`` 已 ``normalized``/``projected`` 且非 delete → 跳过
       （重复 NOTIFY / recover 已处理事件不重复处理）。
    2. service 层：``log_writer.exists`` 按 ``event_id`` 去重（崩溃恢复后最终一致）。

纠错链（§5.1）：``correct`` 已软删除旧事件，但旧事件的派生行可能仍在；worker 在 normalize
新事件前先软删除旧 ``event_id`` 的派生行，使 State Engine 重算时排除旧值。

事务边界：每条消息独立 ``AsyncSession``，handler 内 commit（架构 §5.2）。
异常隔离：单条失败记日志不抛，避免阻断 EventBus 消费循环（at-least-once，靠
``processing_status=pending`` 扫描补偿，APC-T011 recover_pending）。
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..common.event_bus import EventPayload
from ..events.domain import ObservationEvent, ObservationEventRepository, ProcessingStatus
from .domain import EVENT_TYPE_TO_TABLE
from .service import LogWriter, NormalizationService

_logger = logging.getLogger(__name__)

# 所有 P0 派生表名（纠错链/软删除时遍历软删除旧 event_id 的派生行）。
_P0_TABLES = tuple(EVENT_TYPE_TO_TABLE.values())


@runtime_checkable
class WorkerContext(Protocol):
    """worker 单条消息的处理上下文（APC-T014）。

    封装"加载事件 / 软删除派生行 / 归一化 / 提交"四步，使 worker 的 op 分发/去重/纠错链
    逻辑可脱离 DB 纯单测（注入内存替身）。生产实现 ``SqlAlchemyWorkerContext`` 用真实
    session；测试用内存替身验证分发逻辑。
    """

    async def get_event(self, event_id: str) -> ObservationEvent | None:
        """加载未删除事件（软删除过滤）；不存在/已删除返回 None。"""
        ...

    async def soft_delete_event_logs(self, event_id: str) -> None:
        """软删除 ``event_id`` 在所有 P0 派生表的行（纠错链/事件软删除）。"""
        ...

    async def normalize(self, event: ObservationEvent) -> None:
        """归一化事件（写派生表 + 推进 processing_status=normalized）。"""
        ...

    async def commit(self) -> None:
        """提交本消息事务（架构 §5.2 事务边界在 handler）。"""
        ...


class SqlAlchemyWorkerContext:
    """``WorkerContext`` 的 SQLAlchemy 生产实现（APC-T014）。

    持有请求作用域 ``AsyncSession``，构造 repo / log_writer / service（架构 §5.2）。
    """

    def __init__(self, session: AsyncSession) -> None:
        from ..events.infra.repository import SqlAlchemyObservationEventRepository
        from .infra.log_writer import SqlAlchemyLogWriter

        self._session = session
        self._repo: ObservationEventRepository = SqlAlchemyObservationEventRepository(session)
        self._log_writer: LogWriter = SqlAlchemyLogWriter(session)
        self._service = NormalizationService(repository=self._repo, log_writer=self._log_writer)

    async def get_event(self, event_id: str) -> ObservationEvent | None:
        return await self._repo.get(event_id)

    async def soft_delete_event_logs(self, event_id: str) -> None:
        for table in _P0_TABLES:
            await self._log_writer.soft_delete_by_event(event_id, table)

    async def normalize(self, event: ObservationEvent) -> None:
        await self._service.normalize(event)

    async def commit(self) -> None:
        await self._session.commit()


class NormalizationWorker:
    """Normalization 常驻 worker（EventHandler，APC-T014）。

    生命周期：单例（进程级），由 ``EventWorker.add_handler`` 注入；随 EventWorker
    启动/停止。每条消息独立 ``AsyncSession``，handler 内 commit。

    依赖 ``session_factory``（async_sessionmaker）按消息构造请求作用域 session 与
    ``WorkerContext``（架构 §5.2）。``context_factory`` 可注入用于测试替身。
    """

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        context_factory: Callable[[AsyncSession], WorkerContext] | None = None,
        state_recompute: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._context_factory: Callable[[AsyncSession], WorkerContext] = (
            context_factory or SqlAlchemyWorkerContext
        )
        # APC-T017：归一化/软删除成功后触发 State Engine 增量重算（按 baby_id）。
        # 可选注入；None 则不触发（T014 单测默认不接 State Engine）。main 装配时注入
        # 调 StateEngine.recompute(baby_id) 的闭包，打通 Event→Normalization→State 链路。
        self._state_recompute = state_recompute

    async def __call__(self, payload: EventPayload) -> None:
        """``EventHandler`` 协议入口（``EventWorker`` 以 ``await handler(payload)`` 调用）。

        转发到 ``handle``，保持 ``handle`` 为可独立测试的命名方法。
        """
        await self.handle(payload)

    async def handle(self, payload: EventPayload) -> None:
        """处理单条 events.changed 消息（EventHandler 协议）。

        异常隔离：捕获并记日志，不向上抛出（避免阻断 EventBus 消费循环）。
        at-least-once 语义下，未推进 ``processing_status`` 的事件会被
        ``EventWorker.recover_pending`` 重新投递补偿（APC-T011）。
        """
        event_id = payload.get("event_id")
        op = str(payload.get("op", "")).lower()
        baby_id = payload.get("baby_id")
        if not event_id:
            _logger.warning("normalization.worker.skip no event_id payload=%s", payload)
            return
        try:
            if op == "delete":
                await self._handle_delete(str(event_id), baby_id)
            else:
                # insert / update / recover / 未知 op 一律按"处理事件"路径（保守补处理）。
                await self._handle_upsert(str(event_id), baby_id)
        except Exception:  # 异常隔离，不阻断消费循环。
            _logger.exception("normalization.worker.error event_id=%s op=%s", event_id, op)

    async def _handle_upsert(self, event_id: str, baby_id: Any = None) -> None:
        """处理 insert/update/recover：去重 → 纠错链 → normalize → 触发 state 重算。"""
        async with self._session_factory() as session:
            ctx = self._context_factory(session)
            event = await ctx.get_event(event_id)
            if event is None:
                # 事件不存在或已软删除（get_event 过滤 is_deleted）——可能是 delete 后的
                # 残留 NOTIFY，或事件尚未落库。跳过；recover_pending 会重投 pending 事件。
                _logger.info("normalization.worker.skip event not found event_id=%s", event_id)
                return
            # 去重（APC-T014）：processing_status 已推进则跳过，避免重复 NOTIFY 重复处理。
            if event.processing_status in (ProcessingStatus.NORMALIZED, ProcessingStatus.PROJECTED):
                _logger.debug(
                    "normalization.worker.dedup already processed event_id=%s status=%s",
                    event_id,
                    event.processing_status.value,
                )
                return
            # 纠错链（§5.1）：correction_of 非空 → 先软删除旧 event_id 的派生行。
            # 旧事件已被 EventService.correct 软删除，但其派生行可能仍在；软删除使其失效，
            # State Engine 重算时排除旧值。
            if event.correction_of:
                await ctx.soft_delete_event_logs(event.correction_of)

            await ctx.normalize(event)
            await ctx.commit()
        # APC-T017：归一化成功后触发 State Engine 增量重算（按 event.baby_id，比 payload 可靠）。
        await self._trigger_state_recompute(event.baby_id)

    async def _handle_delete(self, event_id: str, baby_id: Any = None) -> None:
        """处理 delete：软删除派生行 → 触发 state 重算（派生表排除后重算）。"""
        async with self._session_factory() as session:
            ctx = self._context_factory(session)
            await ctx.soft_delete_event_logs(event_id)
            await ctx.commit()
        # APC-T017：软删除派生行后触发 State Engine 重算（事件已删，用 payload baby_id）。
        if baby_id is not None:
            await self._trigger_state_recompute(str(baby_id))

    async def _trigger_state_recompute(self, baby_id: str) -> None:
        """触发 State Engine 增量重算（APC-T017，可选）。

        未注入 ``state_recompute`` 时跳过（T014 单测默认不接 State Engine）。
        重算失败不阻断归一化结果（归一化已 commit；重算可由下次事件/recover 补偿）。
        """
        if self._state_recompute is None:
            return
        try:
            await self._state_recompute(baby_id)
        except Exception:  # 重算失败不阻断归一化；at-least-once 靠后续事件/recover 补偿。
            _logger.exception("normalization.worker.state_recompute.error baby_id=%s", baby_id)


__all__ = ["NormalizationWorker", "SqlAlchemyWorkerContext", "WorkerContext"]
