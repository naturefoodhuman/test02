# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""OpenTelemetry tracing setup.

The setup is intentionally local-only by default. If no exporter endpoint is configured,
tracing uses the SDK provider without external network output and therefore safely
degrades when Jaeger/OTLP is absent.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from server.app.settings import Settings


def configure_tracing(settings: Settings) -> None:
    """Configure an OpenTelemetry tracer provider if enabled."""

    if not settings.observability.tracing_enabled:
        return
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        return
    provider = TracerProvider(
        resource=Resource.create({"service.name": settings.observability.service_name})
    )
    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> trace.Tracer:
    """Return a tracer by module name."""

    return trace.get_tracer(name)
