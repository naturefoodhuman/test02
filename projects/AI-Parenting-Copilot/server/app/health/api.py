# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 23:32:00


"""Health endpoints for local operation and future device monitoring."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request

from server.app.common.clock import utc_now
from server.app.di import AppContainer
from server.app.health.monitor import DeviceHealthMonitor
from server.app.notification.sqlalchemy_alert_repo import SQLAlchemyAlertRepository
from server.app.observability.request_audit import record_request_audit

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
    """System health endpoint with latest service/device probe snapshot."""

    container = _container(request)
    monitor = getattr(request.app.state, "device_health_monitor", None)
    probe_snapshot = monitor.snapshot() if monitor is not None else {}
    degraded = any(status == "offline" for status in probe_snapshot.values())
    return {
        "status": "degraded" if degraded else "ok",
        "registered_workers": len(container.worker_registry.workers),
        "checks": {
            "api": "ok",
            "database": container.settings.db_mode,
            "tracing": "enabled"
            if container.settings.observability.tracing_enabled
            else "disabled",
        },
        "device_health": probe_snapshot,
    }


@router.post("/api/v1/system/health/check")
async def run_system_health_check(
    request: Request,
    family_id: str = "dev-family",
    baby_id: str = "dev-baby",
) -> dict[str, Any]:
    """Manually run configured health probes and return statuses."""

    monitor = getattr(request.app.state, "device_health_monitor", None)
    if monitor is None:
        return {"status": "degraded", "checks": {}, "message": "health monitor unavailable"}
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        request_monitor = DeviceHealthMonitor(
            monitor.probes,
            SQLAlchemyAlertRepository(db_session),
        )
        results = await request_monitor.run_once(family_id=family_id, baby_id=baby_id)
        monitor.last_results.update(request_monitor.last_results)
    else:
        results = await monitor.run_once(family_id=family_id, baby_id=baby_id)
    checks = {result.name: result.status.value for result in results}
    response = {
        "status": "degraded" if any(status == "offline" for status in checks.values()) else "ok",
        "checks": checks,
    }
    await record_request_audit(
        request,
        action="system.health_check",
        resource="system_health",
        after=response,
    )
    return response
