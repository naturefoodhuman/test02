# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# gateway/exception_handlers.py —— 全局异常处理器（领域异常 → HTTP 错误信封）。
# 依据：TASK_BACKLOG APC-T002（全局异常格式 {code,message,evidence,trace_id}）；
#       ENGINEERING_DESIGN §5（领域异常层次）；ARCHITECTURE_FINAL §15（API 风格）。
# 设计：领域层抛 DomainError 子类（不感知 HTTP）；本模块统一映射为 HTTP 状态 + ErrorEnvelope。
#       FastAPI 自带异常（RequestValidationError 等）也归一为同一信封，保证响应格式一致。

"""全局异常处理器（领域异常 → HTTP 错误信封）。

领域层只抛 ``DomainError`` 子类（不感知 HTTP）；本模块统一映射为
HTTP 状态码 + ``ErrorEnvelope``（``{code,message,evidence,trace_id}``）。
FastAPI 自带异常（``RequestValidationError`` 等）也归一为同一信封，
保证响应格式一致（架构 §15 API 风格）。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..common.errors import DomainError, ErrorEnvelope
from ..common.ids import new_id

logger = logging.getLogger(__name__)


def _envelope(
    code: str,
    message: str,
    *,
    http_status: int,
    evidence: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> JSONResponse:
    """构造统一错误信封响应。"""
    env = ErrorEnvelope(
        code=code,
        message=message,
        evidence=evidence,
        trace_id=trace_id or new_id(),
    )
    return JSONResponse(status_code=http_status, content=env.model_dump())


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """处理领域异常：按 exc.http_status / exc.code 映射。"""
    logger.info(
        "domain_error code=%s status=%s trace_id=%s path=%s",
        exc.code,
        exc.http_status,
        exc.trace_id,
        request.url.path,
    )
    return _envelope(
        exc.code,
        exc.message,
        http_status=exc.http_status,
        evidence=dict(exc.evidence) if exc.evidence else None,
        trace_id=exc.trace_id,
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI 请求校验失败 → 422 + 统一信封。"""
    trace_id = new_id()
    logger.info(
        "validation_error status=422 trace_id=%s path=%s",
        trace_id,
        request.url.path,
    )
    return _envelope(
        "PARENTING.VALIDATION",
        "请求参数校验失败",
        http_status=422,
        evidence={"errors": exc.errors()},
        trace_id=trace_id,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Starlette/FastAPI HTTPException → 统一信封（保留原 status）。"""
    trace_id = new_id()
    logger.info(
        "http_exception status=%s trace_id=%s path=%s",
        exc.status_code,
        trace_id,
        request.url.path,
    )
    return _envelope(
        f"PARENTING.HTTP_{exc.status_code}",
        str(exc.detail) if exc.detail else "HTTP error",
        http_status=exc.status_code,
        trace_id=trace_id,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：未捕获异常 → 500 + 统一信封（不泄露内部细节）。"""
    trace_id = new_id()
    logger.exception("unhandled_exception trace_id=%s path=%s", trace_id, request.url.path)
    return _envelope(
        "PARENTING.INTERNAL",
        "内部错误，请联系管理员（trace_id 可供排障）",
        http_status=500,
        trace_id=trace_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册全部全局异常处理器到 FastAPI 应用。

    Starlette ``add_exception_handler`` 期望 handler 签名为 ``(Request, Exception)``；
    我们的处理器用具体异常子类以保留类型安全，注册时 cast 到宽签名。
    """
    # Starlette handler 宽签名：Callable[[Request, Exception], JSONResponse | Response]
    Handler = Callable[[Request, Exception], Any]
    app.add_exception_handler(DomainError, cast(Handler, domain_error_handler))
    app.add_exception_handler(
        RequestValidationError, cast(Handler, request_validation_error_handler)
    )
    app.add_exception_handler(StarletteHTTPException, cast(Handler, http_exception_handler))
    app.add_exception_handler(Exception, cast(Handler, unhandled_exception_handler))


__all__ = [
    "domain_error_handler",
    "http_exception_handler",
    "register_exception_handlers",
    "request_validation_error_handler",
    "unhandled_exception_handler",
]
