# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Health endpoints for local operation and future device monitoring."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request

from server.app.common.clock import utc_now
from server.app.di import AppContainer

router = APIRouter(tags=["health"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


@router.get("/healthz")
async def healthz(request: Request) -> dict[str, Any]:
    """Liveness/readiness endpoint that works without DB in dev/mock mode."""

    container = _container(request)
    settings = container.settings
    db_mode = settings.db_mode
    return {
        "status": "ok" if db_mode != "missing" else "degraded",
        "app": settings.app_name,
        "env": settings.env,
        "time": utc_now().isoformat(),
        "dependencies": {
            "database": {
                "mode": db_mode,
                "message": "DB not configured; running in dev/mock mode"
                if db_mode == "dev-mock"
                else "DB configured",
            },
            "model_gateway": {"base_url": str(settings.model_gateway.base_url)},
        },
    }


@router.get("/api/v1/system/health")
async def system_health(request: Request) -> dict[str, Any]:
    """System health endpoint reserved for later device/service probes."""

    container = _container(request)
    return {
        "status": "ok",
        "registered_workers": len(container.worker_registry.workers),
        "checks": {
            "api": "ok",
            "database": container.settings.db_mode,
            "tracing": "enabled"
            if container.settings.observability.tracing_enabled
            else "disabled",
        },
    }
