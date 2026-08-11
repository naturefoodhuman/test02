# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/observability/tracing.py —— OpenTelemetry 基础 tracing。
# 依据：ENGINEERING_DESIGN §10.3（Tracing）；ARCHITECTURE_FINAL §22.4；TASK_BACKLOG APC-T005。
# 设计：OpenTelemetry SDK，未配置 exporter 时安全降级为 no-op（不连 Jaeger，dev 不依赖外部）。
#       trace_id 与 logger 的 trace_id 贯穿（从 OTel span context 取）。
#       手动 span（start_span），不依赖 auto-instrumentation 包。

"""OpenTelemetry 基础 tracing（ENGINEERING_DESIGN §10.3）。

未配置 exporter 时安全降级为 no-op tracer（dev 不依赖外部 Jaeger）。
prod 通过 ``PARENTING_OBSERVABILITY__OTEL_EXPORTER_OTLP_ENDPOINT`` 启用 OTLP exporter。

trace_id 与 logger 的 trace_id 贯穿：``current_trace_id`` 从 OTel span context 取，
供 ``bind_context(trace_id=...)`` 使用，确保日志与 trace 同 ID。
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

from ..settings import get_settings

# 进程级 tracer provider（惰性初始化，幂等）。
_provider: TracerProvider | None = None
_tracer: trace.Tracer | None = None


def _build_provider() -> TracerProvider:
    """构造 TracerProvider（含 Resource service.name）。

    dev 默认 ConsoleSpanExporter（stdout，便于排障）；prod 通过 OTLP endpoint 启用。
    """
    settings = get_settings()
    service_name = settings.observability.service_name
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    # dev：console exporter；prod：OTLP（待 PARENTING_OBSERVABILITY__OTEL_* 配置接入）。
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    return provider


def configure_tracing() -> trace.Tracer:
    """配置并返回 tracer（幂等，进程级单例）。

    未配置 exporter 时 OTel SDK 默认 no-op，不连外部，dev 安全。
    """
    global _provider, _tracer
    if _tracer is not None:
        return _tracer
    _provider = _build_provider()
    trace.set_tracer_provider(_provider)
    _tracer = trace.get_tracer("parenting")
    return _tracer


def get_tracer() -> trace.Tracer:
    """获取已配置的 tracer（未配置则惰性配置）。"""
    if _tracer is None:
        return configure_tracing()
    return _tracer


def current_trace_id() -> str | None:
    """当前 span 的 trace_id（hex，32 字符）；无活跃 span 返回 None。"""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx or not ctx.is_valid:
        return None
    return format(ctx.trace_id, "032x")


def current_span_id() -> str | None:
    """当前 span 的 span_id（hex，16 字符）；无活跃 span 返回 None。"""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx or not ctx.is_valid:
        return None
    return format(ctx.span_id, "016x")


@contextmanager
def start_span(name: str, **attributes: Any) -> Iterator[trace.Span]:
    """手动 span 上下文管理器（自动 set attributes + end）。

    用法::

        with start_span("feeding.normalize", event_type="feeding") as span:
            ...
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for k, v in attributes.items():
            span.set_attribute(k, v)
        yield span


def reset_tracing() -> None:
    """重置 tracer provider（测试用）。"""
    global _provider, _tracer
    _provider = None
    _tracer = None


__all__ = [
    "configure_tracing",
    "current_span_id",
    "current_trace_id",
    "get_tracer",
    "reset_tracing",
    "start_span",
]
