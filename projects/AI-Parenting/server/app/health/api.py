# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/health/api.py —— 健康端点与 Metrics 端点路由。
# 依据：ENGINEERING_DESIGN §10.2（/metrics）、§10.5（Device Health）；ARCHITECTURE_FINAL §22；TASK_BACKLOG APC-T005。
# 设计：/readyz 探活 DB（async ping）+ EventBus 状态；/metrics 暴露 Prometheus exposition。
#       /healthz 仍在 main.py（进程存活），本模块提供 /readyz 与 /metrics 注册函数。

"""健康端点与 Metrics 端点路由。

- ``check_db``：async ping DB（``SELECT 1``），失败返回 degraded。
- ``check_event_bus``：EventBus 状态（已启动=ok）。
- ``register_health_routes(app, settings)``：注册 ``/readyz``（增强探活）与 ``/metrics``。
- ``/healthz`` 仍在 ``main.py``（进程存活，不依赖外部）。
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from ..observability.metrics import metrics_response_body


async def check_db(request: Request) -> str:
    """DB 探活：SELECT 1。返回 'ok' / 'degraded'。

    dev/mock 未配 DB 或连接失败时返回 'degraded'（不抛异常，避免 readyz 500）。
    """
    container = request.app.state.container
    from ..db import get_engine  # 局部导入避免循环

    try:
        engine = get_engine(container.settings)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "degraded"


def check_event_bus(request: Request) -> str:
    """EventBus 探活：已启动返回 'ok'。"""
    container = request.app.state.container
    try:
        # InMemoryEventBus 用 _running 标志；PgListenEventBus（后续任务）同义属性。
        eb = container.event_bus
        running = getattr(eb, "_running", None)
        return "ok" if running else "degraded"
    except Exception:
        return "degraded"


def register_health_routes(app: FastAPI, settings: Any) -> None:
    """注册 /readyz（增强探活）与 /metrics 路由。

    ``/healthz`` 仍在 main.py（进程存活，不依赖外部）。
    """

    @app.get("/readyz", tags=["health"], summary="就绪检查")
    async def readyz(request: Request) -> JSONResponse:
        """就绪探针：DB + EventBus 探活（§10.5 Device Health 基础）。

        dev/mock 未配 DB 时 db=degraded，整体 status=degraded 但进程仍存活。
        """
        db_status = await check_db(request)
        eb_status = check_event_bus(request)
        checks = {"db": db_status, "event_bus": eb_status}
        overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        status_code = 200 if overall == "ok" else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall,
                "env": settings.env,
                "version": "0.1.0",
                "checks": checks,
            },
        )

    @app.get("/metrics", tags=["observability"], summary="Prometheus 指标")
    async def metrics() -> PlainTextResponse:
        """Prometheus exposition 格式指标（§10.2）。"""
        return PlainTextResponse(
            metrics_response_body(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )


__all__ = ["check_db", "check_event_bus", "register_health_routes"]
