# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""FastAPI application shell for AI Parenting Copilot."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI

from server.app.di import AppContainer, create_container
from server.app.gateway.exception_handlers import register_exception_handlers
from server.app.gateway.middleware.logging import RequestLoggingMiddleware
from server.app.health.api import router as health_router
from server.app.observability.logger import configure_logging
from server.app.observability.metrics import metrics_response, set_app_info
from server.app.observability.tracing import configure_tracing
from server.app.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI app without opening DB connections."""

    container = create_container(settings)
    configure_logging(container.settings)
    configure_tracing(container.settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = container
        set_app_info(
            env=container.settings.env,
            db_mode=container.settings.db_mode,
            worker_count=len(container.worker_registry.workers),
        )
        await container.worker_registry.start_all()
        try:
            yield
        finally:
            await container.worker_registry.stop_all()

    app = FastAPI(
        title=container.settings.app_name,
        version="0.1.0",
        description="Local-first AI Parenting Copilot API shell.",
        lifespan=lifespan,
    )
    app.state.container = container
    register_exception_handlers(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(health_router)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> object:
        return metrics_response()

    return app


app = create_app()


def get_app_container(application: FastAPI) -> AppContainer:
    """Expose the typed app container for tests and future routers."""

    return cast(AppContainer, application.state.container)
