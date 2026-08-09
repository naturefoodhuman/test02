# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# app/main.py —— FastAPI 应用入口（应用壳）。
# 依据：ENGINEERING_DESIGN §1.3（进程拓扑：单进程 FastAPI + 内嵌 asyncio worker）；
#       §5（核心抽象）；§8（配置）；ARCHITECTURE_FINAL §15（API）；TASK_BACKLOG APC-T002。
# 设计：装配应用、注册全局异常处理器、暴露 /healthz、预留 worker 注册接口。
#       T002 不实现业务 worker（MQTT/Camera/Normalization 等在各自任务接入）。
#       dev/mock 模式未配 DB 亦可启动（APC-T002 验收）。

"""FastAPI 应用入口（应用壳）。

进程拓扑（ENGINEERING_DESIGN §1.3）：单进程 FastAPI + 内嵌 asyncio worker
（``asyncio.TaskGroup``），常驻消费者（MQTT/Camera/Scheduler/Normalization/
Notification 升级计时）与 HTTP 服务共享事件循环。

APC-T002 范围：装配应用、注册全局异常处理器、暴露 ``/healthz``、
预留 worker 注册接口（``register_worker``）。本任务不实现业务 worker
（业务 worker 在各自任务接入，通过 ``register_worker`` 注册到 startup）。
dev/mock 模式未配 DB 亦可启动（APC-T002 验收标准）。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, Coroutine

from fastapi import FastAPI
from pydantic import BaseModel

from .common.event_bus import EventBus
from .di import Container, build_container
from .gateway.exception_handlers import register_exception_handlers
from .settings import Settings, get_settings

logger = logging.getLogger(__name__)

# ---- Worker 注册接口（预留，APC-T002 不实现业务 worker） ----
# Worker 协议：async 启动协程，返回 None；lifespan 在 startup 阶段以 TaskGroup 调度。
# 用 Coroutine 而非 Awaitable，以匹配 asyncio.create_task 的签名要求。
Worker = Callable[[Container], Coroutine[Any, Any, None]]

# 进程级 worker 注册表：业务模块在各自任务通过 register_worker 注册。
# lifespan startup 时统一以 asyncio.TaskGroup 调度，shutdown 时取消。
_workers: list[Worker] = []


def register_worker(worker: Worker) -> None:
    """注册常驻 worker（业务模块在各自任务调用）。

    APC-T002 仅提供注册机制，不注册任何业务 worker。
    后续任务（MQTT/Camera/Normalization/Notification 升级计时）通过本接口接入。
    """
    _workers.append(worker)
    logger.debug("worker registered: %s", getattr(worker, "__name__", worker))


def clear_workers() -> None:
    """清空 worker 注册表（测试用）。"""
    _workers.clear()


# ---- Health 响应模型 ----


class HealthResponse(BaseModel):
    """健康检查响应（架构 §22 可观测性）。"""

    status: str  # "ok" | "degraded"
    env: str
    version: str
    # 各依赖健康子状态；T002 仅占位，DB/MQTT 探活在各自任务接入。
    checks: dict[str, str] = {}


# ---- 应用工厂 ----


def create_app(settings: Settings | None = None) -> FastAPI:
    """构造 FastAPI 应用（可注入 Settings，便于测试）。

    生命周期（lifespan）：
        - startup：装配 Container、启动 EventBus、调度已注册 worker（TaskGroup）。
        - shutdown：停止 EventBus、取消 worker。
    """
    s = settings or get_settings()
    _configure_logging(s)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 装配进程级容器并挂到 app.state，供 Depends 工厂取用。
        container = build_container(s)
        app.state.container = container

        logger.info(
            "parenting-server starting env=%s http=%s:%s fake_model=%s",
            s.env,
            s.http.host,
            s.http.port,
            s.models.use_fake_client,
        )
        if s.is_dev:
            logger.info("dev/mock 模式：EventBus=InMemoryEventBus，未接真实 DB/MQTT（APC-T002）")

        # 启动事件总线（dev 用 InMemoryEventBus，no-op）。
        event_bus: EventBus = container.event_bus
        await event_bus.start()

        # 调度已注册 worker（T002 无业务 worker，TaskGroup 为空即立即结束上下文管理）。
        # 使用 anyio TaskGroup 风格：保持引用以便 shutdown 取消。
        import asyncio

        worker_tasks: list[asyncio.Task[Any]] = []
        for w in _workers:
            worker_tasks.append(
                asyncio.create_task(w(container), name=getattr(w, "__name__", "worker"))
            )

        try:
            yield
        finally:
            # 取消 worker
            for t in worker_tasks:
                t.cancel()
            for t in worker_tasks:
                try:
                    await t
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("worker exited with error during shutdown")
            await event_bus.stop()
            logger.info("parenting-server stopped")

    app = FastAPI(
        title="AI Parenting Copilot",
        description="家庭私有化 AI 育儿副驾驶系统（FORGE Factory 孵化项目）",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 全局异常处理器
    register_exception_handlers(app)

    # ---- 健康检查端点 ----
    @app.get("/healthz", tags=["health"], summary="健康检查")
    async def healthz() -> HealthResponse:
        """存活探针：返回应用与依赖健康状态。

        T002 仅返回进程存活 + env/version；DB/MQTT 探活在各自任务接入 checks。
        dev/mock 模式无 DB 连接，status=ok（进程存活即健康）。
        """
        checks: dict[str, str] = {"event_bus": "ok"}
        return HealthResponse(status="ok", env=s.env, version="0.1.0", checks=checks)

    @app.get("/readyz", tags=["health"], summary="就绪检查")
    async def readyz() -> HealthResponse:
        """就绪探针：依赖就绪判定。

        T002 占位：dev 模式直接 ready；prod 在各自任务接入 DB/MQTT 探活。
        """
        return HealthResponse(status="ok", env=s.env, version="0.1.0", checks={"event_bus": "ok"})

    return app


def _configure_logging(settings: Settings) -> None:
    """按 settings.observability 配置根日志（架构 §22）。

    T002 用标准 logging；structlog/prometheus 在可观测性任务接入。
    """
    level = getattr(logging, settings.observability.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


# 模块级 app 单例：供 `uvicorn server.app.main:app` 启动（APC-T002 验收）。
app = create_app()


__all__ = ["HealthResponse", "app", "clear_workers", "create_app", "register_worker"]
