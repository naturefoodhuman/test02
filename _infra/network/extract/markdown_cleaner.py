"""
Markdown Cleaner (FORGE Network incremental)

Task: E4-C2-S1-T3

Per TASK_BACKLOG + NETWORK_ENGINEERING_DESIGN §6.4

Responsibilities:
- Remove excessive blank lines
- Strip inline ads / tracking junk
- Enforce max length (default 8000 chars)
- Optional chunking for long content
- Keep provenance / source metadata if present
"""

from __future__ import annotations

import re
from typing import List

from .models import ExtractResult


def clean_markdown(
    content: str,
    max_chars: int = 8000,
    remove_ads: bool = True,
) -> str:
    """
    Clean and normalize extracted Markdown.

    - Collapses 3+ blank lines to 2
    - Removes common ad / tracking patterns
    - Truncates to max_chars (preserves beginning)
    """
    if not content:
        return ""

    text = content

    # 1. Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 2. Remove common ad / noise patterns (lightweight, no heavy regex)
    if remove_ads:
        ad_patterns = [
            r"\[广告\]",
            r"广告\s*[:：]",
            r"赞助内容",
            r"Subscribe to our newsletter.*",
            r"Click here to.*",
            r"Read more.*",
            r"^\s*[-–—]{3,}\s*$",  # separators
        ]
        for pat in ad_patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # 3. Strip leading/trailing whitespace per line + overall
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    # 4. Final length control
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[...truncated]"

    return text.strip()


def chunk_markdown(
    content: str,
    chunk_size: int = 4000,
    overlap: int = 200,
) -> List[str]:
    """
    Split long Markdown into overlapping chunks.
    Simple character-based chunker (good enough for Phase 1).
    """
    if not content or len(content) <= chunk_size:
        return [content] if content else []

    chunks: List[str] = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap if end < len(content) else len(content)

    return chunks


def clean_extract_result(result: ExtractResult, max_chars: int = 8000) -> ExtractResult:
    """
    In-place clean an ExtractResult (for markdown mode).
    """
    if result.mode.value == "markdown" and result.content:
        cleaned = clean_markdown(result.content, max_chars=max_chars)
        result.content = cleaned
        result.char_count = len(cleaned)
    return result
