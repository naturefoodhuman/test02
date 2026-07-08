# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Timezone-aware clock helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""

    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    """Ensure a datetime carries timezone information."""

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("datetime must be timezone-aware")
    return value


def to_utc(value: datetime) -> datetime:
    """Convert a timezone-aware datetime to UTC."""

    return ensure_aware(value).astimezone(UTC)
