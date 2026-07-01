# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""ServiceResult for FEOS service methods."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    ok: bool
    value: T | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @classmethod
    def success(cls, value: T | None = None, warnings: list[str] | None = None) -> "ServiceResult[T]":
        return cls(ok=True, value=value, warnings=warnings or [])

    @classmethod
    def failure(cls, errors: list[str] | str, warnings: list[str] | None = None) -> "ServiceResult[T]":
        return cls(ok=False, errors=[errors] if isinstance(errors, str) else errors, warnings=warnings or [])
