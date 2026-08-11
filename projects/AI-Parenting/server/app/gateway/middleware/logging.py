# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# gateway/middleware/logging.py —— 请求日志中间件（structlog + trace_id/request_id 贯穿）。
# 依据：ENGINEERING_DESIGN §10.1（Logging）；ARCHITECTURE_FINAL §22.1；TASK_BACKLOG APC-T005。
# 设计：每请求生成 request_id（ULID），从入站 header 取 trace_id（无则生成），
#       bind_context 注入 structlog contextvars，请求结束 clear_context 防泄漏。
#       记录 method/path/status/duration_ms；PII 经 logger.mask_pii 脱敏。

"""请求日志中间件（structlog + trace_id/request_id 贯穿）。

每请求：
    1. 生成 request_id（ULID），从入站 ``X-Trace-Id`` header 取 trace_id（无则生成 ULID）。
    2. ``bind_context`` 注入 trace_id/request_id/actor_kind/module 到 structlog contextvars。
    3. 响应回写 ``X-Trace-Id`` / ``X-Request-Id`` header，供客户端排障。
    4. 记录 method/path/status/duration_ms（PII 经 mask_pii 脱敏）。
    5. 请求结束 ``clear_context`` 防跨请求泄漏。
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ...common.ids import new_id
from ...observability.logger import bind_context, clear_context, get_logger

logger = get_logger(__name__)

# 入站 trace_id header（与下游服务约定）。
TRACE_ID_HEADER = "X-Trace-Id"
REQUEST_ID_HEADER = "X-Request-Id"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """每请求结构化日志中间件（§10.1）。"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # trace_id：优先用入站 header（贯穿上游链路），无则生成。
        trace_id = request.headers.get(TRACE_ID_HEADER) or new_id()
        request_id = new_id()

        # 注入上下文（actor_kind=api 对 HTTP 请求；module 由 logger 自动带）。
        bind_context(trace_id=trace_id, request_id=request_id, actor_kind="api")

        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            # 回写 header 供客户端排障。
            response.headers[TRACE_ID_HEADER] = trace_id
            response.headers[REQUEST_ID_HEADER] = request_id

            logger.info(
                "request %s %s -> %s duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request %s %s -> error duration_ms=%.1f",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise
        finally:
            clear_context()


def add_request_logging(app: Starlette) -> None:
    """注册请求日志中间件到 FastAPI 应用。"""
    app.add_middleware(RequestLoggingMiddleware)


__all__ = [
    "REQUEST_ID_HEADER",
    "TRACE_ID_HEADER",
    "RequestLoggingMiddleware",
    "add_request_logging",
]
