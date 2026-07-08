# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""FastAPI exception handlers with a stable public error contract."""
from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.app.common.errors import AppError, ErrorResponse


def _trace_id(request: Request) -> str:
    return str(getattr(request.state, "trace_id", getattr(request.state, "request_id", "unknown")))


def _json(status_code: int, payload: ErrorResponse) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload.model_dump())


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map expected application errors to the public contract."""

    return _json(exc.status_code, exc.to_response(trace_id=_trace_id(request)))


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Map Starlette/FastAPI HTTP errors to the public contract."""

    return _json(
        exc.status_code,
        ErrorResponse(
            code="HTTP_ERROR",
            message=str(exc.detail),
            evidence=None,
            trace_id=_trace_id(request),
        ),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Map request validation errors to the public contract."""

    return _json(
        422,
        ErrorResponse(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            evidence={"errors": exc.errors()},
            trace_id=_trace_id(request),
        ),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Hide unexpected internals while preserving traceability."""

    return _json(
        500,
        ErrorResponse(
            code="INTERNAL_ERROR",
            message="Internal server error",
            evidence=None,
            trace_id=_trace_id(request),
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all gateway exception handlers."""

    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)


ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]
