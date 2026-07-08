# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Structured logging setup and PII masking."""
from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping
from typing import Any, cast

import structlog

from server.app.settings import Settings

SENSITIVE_KEYS = {
    "raw_input",
    "media_path",
    "local_path",
    "file_path",
    "password",
    "token",
    "secret",
    "api_key",
    "authorization",
    "cookie",
}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+\d[\d -]{7,}\d|\d{3}[ -]\d{3}[ -]\d{4})(?!\d)")
ISO_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
ULID_TEXT_RE = re.compile(r"^[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}$")


def mask_sensitive(value: Any) -> Any:
    """Recursively mask PII-like values and known sensitive fields."""

    if isinstance(value, Mapping):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str.lower() in SENSITIVE_KEYS:
                masked[key_str] = "***MASKED***"
            else:
                masked[key_str] = mask_sensitive(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(mask_sensitive(item) for item in value)
    if isinstance(value, str):
        if ISO_TIME_RE.match(value) or ULID_TEXT_RE.fullmatch(value):
            return value
        text = EMAIL_RE.sub("***EMAIL***", value)
        return PHONE_RE.sub("***PHONE***", text)
    return value


def _mask_processor(
    _logger: logging.Logger,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    return cast(dict[str, Any], mask_sensitive(event_dict))


def configure_logging(settings: Settings) -> None:
    """Configure stdlib + structlog JSON logging."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        force=True,
    )
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _mask_processor,
    ]
    if settings.observability.json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(module: str) -> structlog.stdlib.BoundLogger:
    """Return a bound logger with required baseline fields present."""

    return cast(
        structlog.stdlib.BoundLogger,
        structlog.get_logger(module).bind(
            module=module,
            trace_id=None,
            request_id=None,
            family_id=None,
            baby_id=None,
            user_id=None,
            actor_kind=None,
        ),
    )
