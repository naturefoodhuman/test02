# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Application error hierarchy and response contract."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

Evidence = Mapping[str, Any] | None


class ErrorResponse(BaseModel):
    """Public error response contract: {code,message,evidence,trace_id}."""

    code: str
    message: str
    evidence: dict[str, Any] | None = None
    trace_id: str = Field(default="unknown")


class AppError(Exception):
    """Base class for expected application errors."""

    status_code: int = 400
    code: str = "APP_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        evidence: Evidence = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.evidence = dict(evidence) if evidence is not None else None

    def to_response(self, trace_id: str) -> ErrorResponse:
        """Convert the exception into the public response model."""

        return ErrorResponse(
            code=self.code,
            message=self.message,
            evidence=self.evidence,
            trace_id=trace_id,
        )


class ConfigurationError(AppError):
    """Raised when required runtime configuration is invalid."""

    status_code = 500
    code = "CONFIGURATION_ERROR"


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    """Raised on idempotency or state conflicts."""

    status_code = 409
    code = "CONFLICT"
