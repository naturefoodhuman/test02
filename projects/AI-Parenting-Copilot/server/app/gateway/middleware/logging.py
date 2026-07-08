# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""HTTP request logging and metrics middleware."""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from server.app.common.ids import new_ulid
from server.app.observability.metrics import record_http_request


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach request/trace IDs, emit structured logs and record metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id", new_ulid())
        trace_id = request.headers.get("x-trace-id", request_id)
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        logger = structlog.get_logger("http").bind(
            module="gateway",
            request_id=request_id,
            trace_id=trace_id,
            family_id=request.headers.get("x-family-id"),
            baby_id=request.headers.get("x-baby-id"),
            user_id=request.headers.get("x-user-id"),
            actor_kind=request.headers.get("x-actor-kind", "anonymous"),
            method=request.method,
            path=request.url.path,
        )
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            record_http_request(request.method, request.url.path, status_code, duration)
            logger.info(
                "http_request",
                status_code=status_code,
                duration_ms=round(duration * 1000, 3),
            )
            if "response" in locals():
                response.headers["x-request-id"] = request_id
                response.headers["x-trace-id"] = trace_id
