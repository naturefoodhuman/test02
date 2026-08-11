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

import asyncio
import contextlib
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


def parse_event_payload(raw: str) -> EventPayload:
    """解析 PG NOTIFY payload（JSON 字符串）为 dict（APC-T011 单元测试目标）。

    NOTIFY payload 由 trigger 用 ``json_build_object`` 构造、``p::text`` 转字符串。
    本函数反序列化并校验关键字段（event_id/baby_id/op）存在。

    Raises:
        ValueError: payload 不是合法 JSON 或缺少 event_id/baby_id/op 字段。
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid NOTIFY payload JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"NOTIFY payload must be a JSON object, got {type(data).__name__}")
    for key in ("event_id", "baby_id", "op"):
        if key not in data:
            raise ValueError(f"NOTIFY payload missing required field: {key}")
    return data


class PgListenEventBus:
    """PG LISTEN/NOTIFY 事件总线实现（APC-T011）。

    用独立 ``asyncpg`` 连接监听 ``events.changed`` channel（不与 SQLAlchemy 池混用，
    避免 LISTEN 长连接阻塞业务连接池）。payload 由 trigger 构造为 JSON 字符串
    （``event_id``/``baby_id``/``family_id``/``op``），经 ``parse_event_payload`` 反序列化。

    at-least-once 投递：handler 抛异常仅记录日志（不重投 NOTIFY，因 NOTIFY 已消费即丢失）；
    业务幂等由消费方保证（worker 用 ``processing_status=pending`` 扫描做崩溃恢复，
    架构 §11 / §730）。这是 PG LISTEN/NOTIFY 的标准取舍——NOTIFY 不持久化，
    崩溃恢复依赖状态扫描而非消息重投。

    生命周期：单例（进程级），由 DI 容器持有；``start``/``stop`` 在 lifespan 调用。
    """

    def __init__(self, dsn: str) -> None:
        """``dsn`` 为纯 ``postgresql://`` 连接串（剥离 SQLAlchemy ``+asyncpg`` 前缀）。"""
        self._dsn = dsn
        self._handlers: dict[str, list[EventHandler]] = {}
        self._conn: Any = None  # asyncpg.Connection | None
        self._queue: asyncio.Queue[tuple[str, str]] | None = None
        self._listen_task: Any = None  # asyncio.Task | None
        self._running = False

    async def subscribe(self, channel: str, handler: EventHandler) -> None:
        self._handlers.setdefault(channel, []).append(handler)
        logger.debug("PgListenEventBus subscribed channel=%s", channel)

    async def publish(self, channel: str, payload: EventPayload) -> None:
        """主动发布（``SELECT pg_notify``），供测试与进程内触发。

        生产路径由 DB trigger 自动 NOTIFY，无需调用本方法；本方法用于测试主动触发。
        """
        import asyncpg  # 延迟导入避免无 DB 环境加载失败

        if self._conn is None:
            self._conn = await asyncpg.connect(self._dsn)
        await self._conn.execute(
            "SELECT pg_notify($1, $2)", channel, json.dumps(payload, default=str)
        )

    def _on_notification(self, conn: Any, pid: int, channel: str, payload: str) -> None:
        """asyncpg ``add_listener`` 回调（同步）：把 notification 投递到 queue 供消费循环处理。"""
        if self._queue is not None:
            self._queue.put_nowait((channel, payload))

    async def start(self) -> None:
        """建立独立连接、``add_listener`` 订阅各 channel、启动消费循环。"""
        import asyncpg

        self._conn = await asyncpg.connect(self._dsn)
        self._queue = asyncio.Queue()
        for channel in self._handlers:
            await self._conn.add_listener(channel, self._on_notification)
        self._running = True
        self._listen_task = asyncio.create_task(self._consume_loop())
        logger.info("PgListenEventBus started, listening channels=%s", list(self._handlers))

    async def _consume_loop(self) -> None:
        """消费 ``_queue`` 中的 notification，反序列化 payload 调用 handler。"""
        assert self._queue is not None
        try:
            while self._running:
                channel, raw_payload = await self._queue.get()
                handlers = self._handlers.get(channel, [])
                try:
                    payload = parse_event_payload(raw_payload)
                except ValueError as exc:
                    logger.warning("PgListenEventBus dropped malformed payload: %s", exc)
                    continue
                for handler in handlers:
                    try:
                        await handler(payload)
                    except Exception:  # at-least-once 由 worker 幂等保证
                        logger.exception(
                            "PgListenEventBus handler error on channel=%s event_id=%s",
                            channel,
                            payload.get("event_id"),
                        )
        except asyncio.CancelledError:
            logger.info("PgListenEventBus consume loop cancelled")

    async def stop(self) -> None:
        """优雅停止：取消消费循环、``remove_listener``、关闭连接。"""
        self._running = False
        if self._listen_task is not None:
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None
        if self._conn is not None:
            try:
                for channel in self._handlers:
                    await self._conn.remove_listener(channel, self._on_notification)
            finally:
                await self._conn.close()
                self._conn = None
        logger.info("PgListenEventBus stopped")


__all__ = [
    "EventBus",
    "EventHandler",
    "EventPayload",
    "InMemoryEventBus",
    "PgListenEventBus",
    "parse_event_payload",
]
