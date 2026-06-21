"""
Extract data models (Pydantic + Enum)

Per TASK_BACKLOG E4-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.2
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractMode(str, Enum):
    """Supported extraction modes."""

    MARKDOWN = "markdown"
    HTML_STRIPPED = "html_stripped"
    SCREENSHOT = "screenshot"   # requires approval in most policies


class ExtractRequest(BaseModel):
    """Input for content extraction."""

    url: str = Field(..., description="Target URL to extract")
    mode: ExtractMode = ExtractMode.MARKDOWN
    max_chars: int = Field(8000, ge=500, le=200000)
    allow_js: bool = False   # execute_js (security sensitive)
    screenshot_requires_approval: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http(s)://")
        return v


class ExtractResult(BaseModel):
    """Result of content extraction."""

    url: str
    content: str = ""
    mode: ExtractMode
    extractor_used: str = "unknown"   # "crawl4ai", "trafilatura", "playwright"
    error: str | None = None
    char_count: int = 0
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content", mode="after")
    @classmethod
    def compute_char_count(cls, v: str, info: Any) -> str:
        # side-effect: set char_count
        return v

    def model_post_init(self, __context: Any) -> None:
        self.char_count = len(self.content or "")
