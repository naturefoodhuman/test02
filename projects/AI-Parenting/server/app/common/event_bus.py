# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# common/event_bus.py —— PG LISTEN/NOTIFY 轻量事件总线封装。
# 依据：ENGINEERING_DESIGN §5（模块间异步事件通过 PG LISTEN/NOTIFY）；
#       ENGINEERING_DESIGN §7.1（NOTIFY events.changed --> Normalization worker）；
#       ENGINEERING_DESIGN §11（at-least-once + 幂等消费，崩溃恢复用 processing_status）。
# 设计：本任务（APC-T002）只定义协议与占位实现，不接真实 PG 连接
#       （DB 连接在 APC-T003 Alembic 初始化后落地）。
#       协议先行，后续 worker 任务注入真实实现。

"""PG LISTEN/NOTIFY 轻量事件总线封装。

架构选型（ENGINEERING_DESIGN §5/§7.1/§11）：模块间异步事件通过 PG ``LISTEN/NOTIFY``
轻量总线，at-least-once 投递 + 幂等消费，崩溃恢复用 ``processing_status``，避免引入额外消息中间件。

本任务（APC-T002）只定义 ``EventBus`` 协议与进程内占位实现（``InMemoryEventBus``），
不接真实 PG 连接（DB 连接在 APC-T003 Alembic 初始化后落地）。
协议先行，后续 worker 任务注入真实 ``PgListenEventBus`` 实现。
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# 事件载荷类型：NOTIFY payload 为 JSON 字符串，反序列化为 dict。
EventPayload = dict[str, Any]
# 订阅回调：接收事件载荷，返回 None；抛异常视为消费失败（触发 at-least-once 重投）。
EventHandler = Callable[[EventPayload], Awaitable[None]]


@runtime_checkable
class EventBus(Protocol):
    """事件总线协议（PG LISTEN/NOTIFY 抽象）。

    实现方负责：订阅注册、NOTIFY 监听、payload 反序列化、at-least-once 投递、
    幂等消费（依赖 processing_status 状态机，由消费方维护）。
    """

    async def subscribe(self, channel: str, handler: EventHandler) -> None:
        """订阅指定 channel，注册异步处理回调。"""
        ...

    async def publish(self, channel: str, payload: EventPayload) -> None:
        """向指定 channel 发布事件（payload 序列化为 JSON）。"""
        ...

    async def start(self) -> None:
        """启动监听循环（连接 PG、执行 LISTEN、进入消费循环）。"""
        ...

    async def stop(self) -> None:
        """优雅停止监听循环，释放连接。"""
        ...


class InMemoryEventBus:
    """进程内事件总线占位实现（APC-T002）。

    仅用于 dev/mock 模式与单元测试；不跨进程、不持久化、不保证 at-least-once。
    生产路径在 APC-T003+ 由 ``PgListenEventBus`` 替换（DI 注入）。
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._running = False

    async def subscribe(self, channel: str, handler: EventHandler) -> None:
        self._handlers.setdefault(channel, []).append(handler)
        logger.debug("InMemoryEventBus subscribed channel=%s", channel)

    async def publish(self, channel: str, payload: EventPayload) -> None:
        # 序列化/反序列化一遍，模拟 PG NOTIFY 的 JSON payload 边界。
        encoded = json.dumps(payload, default=str)
        decoded: EventPayload = json.loads(encoded)
        for handler in self._handlers.get(channel, []):
            await handler(decoded)

    async def start(self) -> None:
        self._running = True
        logger.info("InMemoryEventBus started (no-op for in-process bus)")

    async def stop(self) -> None:
        self._running = False
        logger.info("InMemoryEventBus stopped")


__all__ = ["EventBus", "EventHandler", "EventPayload", "InMemoryEventBus"]
