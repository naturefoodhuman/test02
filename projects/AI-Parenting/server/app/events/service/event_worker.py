# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/service/event_worker.py —— 事件变更 worker 消费基座（APC-T011）。
# 依据：ENGINEERING_DESIGN §7.1（NOTIFY events.changed --> Normalization worker）、
#       §11（at-least-once + 幂等消费，崩溃恢复用 processing_status）、§6.2（processing_status 状态机）；
#       ARCHITECTURE_FINAL §4.1、§730（PG NOTIFY 消费 幂等 at-least-once 崩溃恢复用 processing_status）；
#       TASK_BACKLOG APC-T011（消费 at-least-once 业务幂等；Worker 崩溃恢复依赖 processing_status=pending 扫描；
#       验收：本地 dev 启动后 worker 能订阅并打印事件变更日志）。
# 设计：订阅 EventBus 的 events.changed channel，handler 记录结构化日志（验收要求）。
#       崩溃恢复：recover_pending() 扫描 processing_status=pending 的事件，重新投递给 handler
#       （at-least-once 语义：NOTIFY 不持久化，崩溃期间错过的通知靠状态扫描补偿）。
#       幂等：消费方（Normalization，APC-T013+）必须幂等——按 event_id 去重 + processing_status 推进。
# 边界：本 worker 只做"订阅 + 日志 + 恢复扫描"，不做归一化（归一化在 normalization 模块，APC-T013）。

"""事件变更 worker 消费基座（APC-T011）。

架构（ENGINEERING_DESIGN §7.1 / §11 / §730）：``observation_event`` 变更经 PG trigger
``NOTIFY events.changed``，worker 经 ``EventBus`` 订阅消费。at-least-once 投递 + 幂等消费，
崩溃恢复用 ``processing_status=pending`` 扫描（NOTIFY 不持久化，错过的通知靠状态扫描补偿）。

本 worker 是消费基座（订阅 + 日志 + 恢复扫描），归一化逻辑在 ``normalization`` 模块（APC-T013+）
通过 ``subscribe`` 注入 handler。P0 阶段 handler 仅记录结构化日志（验收：dev 启动后打印事件变更）。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from ...common.event_bus import EventBus, EventPayload
from ...models.events import ObservationEvent as ObservationEventOrm

logger = logging.getLogger(__name__)

# 事件变更 channel 名（与迁移 0004 trigger 的 pg_notify channel 对齐）。
EVENTS_CHANGED_CHANNEL = "events.changed"


class EventWorker:
    """事件变更 worker（订阅 events.changed + 崩溃恢复扫描）。

    生命周期：单例（进程级），由 DI 容器持有；``start`` 在应用 lifespan 调用，
    ``stop`` 在关闭时调用。handler 由归一化模块（APC-T013+）通过 ``add_handler`` 注入；
    P0 无归一化时用默认日志 handler（验收：打印事件变更）。
    """

    def __init__(
        self,
        *,
        bus: EventBus,
        session_factory: Any,  # async_sessionmaker
    ) -> None:
        self._bus = bus
        self._session_factory = session_factory
        self._handlers: list[Any] = []  # list[EventHandler]

    def add_handler(self, handler: Any) -> None:
        """注册事件变更 handler（归一化模块注入，APC-T013+）。"""
        self._handlers.append(handler)

    async def start(self) -> None:
        """订阅 events.changed 并启动 EventBus 监听循环。

        P0 默认 handler：记录结构化日志（验收：dev 启动后 worker 能订阅并打印事件变更）。
        """
        await self._bus.subscribe(EVENTS_CHANGED_CHANNEL, self._dispatch)
        await self._bus.start()
        logger.info("EventWorker started, subscribed channel=%s", EVENTS_CHANGED_CHANNEL)

    async def _dispatch(self, payload: EventPayload) -> None:
        """分发事件给所有已注册 handler；P0 无 handler 时记录日志。"""
        if not self._handlers:
            logger.info(
                "event changed event_id=%s baby_id=%s op=%s",
                payload.get("event_id"),
                payload.get("baby_id"),
                payload.get("op"),
            )
            return
        for handler in self._handlers:
            await handler(payload)

    async def recover_pending(self, limit: int = 500) -> int:
        """崩溃恢复：扫描 ``processing_status=pending`` 事件，重新投递给 handler。

        at-least-once 语义（架构 §11 / §730）：NOTIFY 不持久化，崩溃期间错过的通知
        靠 ``processing_status=pending`` 扫描补偿。归一化完成后由消费方推进状态
        （pending → normalized → projected），未推进的视为未处理，重启后重新投递。

        返回重新投递的事件数。P0 无归一化 handler 时仅记录扫描结果。
        """
        async with self._session_factory() as session:
            stmt = (
                select(ObservationEventOrm)
                .where(
                    ObservationEventOrm.processing_status == "pending",
                    ObservationEventOrm.is_deleted.is_(False),
                )
                .order_by(ObservationEventOrm.start_time.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

        for row in rows:
            payload: EventPayload = {
                "event_id": row.id,
                "baby_id": row.baby_id,
                "family_id": row.family_id,
                "op": "recover",
            }
            if not self._handlers:
                logger.info(
                    "recover pending event_id=%s baby_id=%s",
                    payload["event_id"],
                    payload["baby_id"],
                )
            else:
                for handler in self._handlers:
                    await handler(payload)
        return len(rows)

    async def stop(self) -> None:
        """停止 EventBus 监听循环。"""
        await self._bus.stop()
        logger.info("EventWorker stopped")


__all__ = ["EVENTS_CHANGED_CHANNEL", "EventWorker"]
