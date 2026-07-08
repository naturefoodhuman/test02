# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Prometheus metrics primitives."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from starlette.responses import Response

REGISTRY = CollectorRegistry()

HTTP_REQUESTS_TOTAL = Counter(
    "parenting_http_requests_total",
    "Total HTTP requests handled by AI Parenting Copilot.",
    ["method", "path", "status"],
    registry=REGISTRY,
)
HTTP_REQUEST_SECONDS = Histogram(
    "parenting_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    registry=REGISTRY,
)
REGISTERED_WORKERS = Gauge(
    "parenting_registered_workers",
    "Number of registered in-process background workers.",
    registry=REGISTRY,
)
APP_INFO = Gauge(
    "parenting_app_info",
    "Application info labelled by environment.",
    ["env", "db_mode"],
    registry=REGISTRY,
)


def record_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Record request count and latency."""

    status = str(status_code)
    HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=status).inc()
    HTTP_REQUEST_SECONDS.labels(method=method, path=path).observe(duration_seconds)


def set_app_info(env: str, db_mode: str, worker_count: int) -> None:
    """Set process-level gauges."""

    APP_INFO.labels(env=env, db_mode=db_mode).set(1)
    REGISTERED_WORKERS.set(worker_count)


def metrics_response() -> Response:
    """Return current Prometheus metrics as a Starlette response."""

    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
