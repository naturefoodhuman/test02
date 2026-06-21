"""
Search data models (Pydantic, FORGE Network incremental)

Follows TASK_BACKLOG E3-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.1
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class SearchQuery(BaseModel):
    """Search input model."""

    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(20, ge=1, le=100)
    engines: list[str] | None = None
    language: str = "zh"  # or "en"
    safe_search: bool = True

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query cannot be empty")
        return v


class SearchResult(BaseModel):
    """Normalized search result."""

    url: str
    title: str = ""
    snippet: str = ""
    domain: str = ""
    score: float = Field(0.0, ge=0.0, le=1.0)
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http(s)://")
        return v

    @model_validator(mode="after")
    def compute_domain(self) -> "SearchResult":
        if not self.domain and self.url:
            try:
                parsed = urlparse(self.url)
                self.domain = parsed.netloc.lower()
            except Exception:
                self.domain = ""
        return self
