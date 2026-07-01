# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Shared Pydantic helpers for FEOS domain models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Type, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="FEOSModel")


class FEOSModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2, exclude_none=True)

    def to_yaml_text(self) -> str:
        return yaml.safe_dump(self.to_dict(), allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml_text(cls: Type[T], text: str) -> T:
        data = yaml.safe_load(text) or {}
        return cls(**data)

    @classmethod
    def from_yaml_file(cls: Type[T], path: Path) -> T:
        return cls.from_yaml_text(path.read_text(encoding="utf-8"))
