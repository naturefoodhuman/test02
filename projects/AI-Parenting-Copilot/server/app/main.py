# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 01:10:00


"""FastAPI application shell for AI Parenting Copilot."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI

from server.app.auth.api.routes import router as auth_router
from server.app.auth.infra.repository import InMemoryAuthRepository
from server.app.auth.service.auth_service import AuthService
from server.app.auth.service.jwt_service import JWTService
from server.app.auth.service.passwords import PasswordHasher
from server.app.camera.api.routes import router as camera_router
from server.app.camera.sleep_session import InMemorySleepSessionRepository
from server.app.db import create_optional_engine, create_session_factory
from server.app.di import AppContainer, create_container
from server.app.events.api.routes import router as events_router
from server.app.events.infra.repository import InMemoryEventRepository
from server.app.export.service import ExportService
from server.app.gateway.exception_handlers import register_exception_handlers
from server.app.gateway.middleware.logging import RequestLoggingMiddleware
from server.app.health.api import router as health_router
from server.app.health.monitor import DeviceHealthMonitor
from server.app.media.api.routes import router as media_router
from server.app.media.storage import MediaStorageService
from server.app.normalization.service import InMemoryDerivedTableStore, NormalizationService
from server.app.normalization.worker import PostgresEventNormalizationWorker
from server.app.notification.alert_repo import InMemoryAlertRepository
from server.app.notification.api.routes import router as alert_router
from server.app.notification.delivery_repo import InMemoryDeliveryRepository
from server.app.observability.audit import MemoryAuditSink
from server.app.observability.logger import configure_logging
from server.app.observability.metrics import metrics_response, set_app_info
from server.app.observability.tracing import configure_tracing
from server.app.orchestrator.api.routes import router as orchestrator_router
from server.app.orchestrator.orchestrator import Orchestrator
from server.app.rule_engine.api.routes import router as rules_router
from server.app.rule_engine.evidence_repo import InMemoryEvidencePolicyRepository
from server.app.settings import Settings
from server.app.state_engine.api.routes import router as state_router
from server.app.state_engine.engine import BabyStateEngine
from server.app.state_engine.snapshot_repo import InMemoryStateSnapshotRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI app without opening DB connections."""

    container = create_container(settings)
    configure_logging(container.settings)
    configure_tracing(container.settings)
    db_engine = create_optional_engine(container.settings)
    db_session_factory = create_session_factory(db_engine) if db_engine is not None else None
    if db_session_factory is not None and container.settings.database.url:
        container.worker_registry.register(
            PostgresEventNormalizationWorker(
                database_url=container.settings.database.url,
                session_factory=db_session_factory,
            )
        )

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
            if db_engine is not None:
                await db_engine.dispose()

    app = FastAPI(
        title=container.settings.app_name,
        version="0.1.0",
        description="Local-first AI Parenting Copilot API shell.",
        lifespan=lifespan,
    )
    app.state.container = container
    app.state.db_engine = db_engine
    app.state.db_session_factory = db_session_factory
    app.state.audit_sink = MemoryAuditSink()
    app.state.alert_repository = InMemoryAlertRepository(app.state.audit_sink)
    app.state.notification_delivery_repo = InMemoryDeliveryRepository()
    app.state.device_health_monitor = DeviceHealthMonitor([], app.state.alert_repository)
    app.state.sleep_session_repository = InMemorySleepSessionRepository(app.state.audit_sink)
    app.state.event_repository = InMemoryEventRepository()
    app.state.derived_table_store = InMemoryDerivedTableStore()
    app.state.normalization_service = NormalizationService(app.state.derived_table_store)
    app.state.state_snapshot_repository = InMemoryStateSnapshotRepository()
    app.state.state_engine = BabyStateEngine(app.state.state_snapshot_repository)
    app.state.evidence_policy_repo = InMemoryEvidencePolicyRepository()
    app.state.media_storage = MediaStorageService()
    app.state.export_service = ExportService()
    app.state.orchestrator = Orchestrator(audit_sink=app.state.audit_sink)
    app.state.auth_service = AuthService(
        InMemoryAuthRepository(),
        JWTService(
            container.settings.auth.jwt_secret,
            ttl_seconds=container.settings.auth.access_token_ttl_seconds,
        ),
        PasswordHasher(),
    )
    register_exception_handlers(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(events_router)
    app.include_router(orchestrator_router)
    app.include_router(alert_router)
    app.include_router(camera_router)
    app.include_router(media_router)
    app.include_router(state_router)
    app.include_router(rules_router)

    @app.middleware("http")
    async def db_session_middleware(request, call_next):  # type: ignore[no-untyped-def]
        session_factory = getattr(request.app.state, "db_session_factory", None)
        if session_factory is None:
            return await call_next(request)
        async with session_factory() as session:
            request.state.db_session = session
            response = await call_next(request)
            if response.status_code < 400:
                await session.commit()
            else:
                await session.rollback()
            return response

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> object:
        return metrics_response()

    return app


app = create_app()


def get_app_container(application: FastAPI) -> AppContainer:
    """Expose the typed app container for tests and future routers."""

    return cast(AppContainer, application.state.container)
