# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:55:00

"""Local RAG data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class DocumentInput:
    source_url: str
    content: str
    title: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StoredDocument:
    id: str
    source_url: str
    title: str | None
    raw_hash: str


@dataclass(frozen=True)
class StoredChunk:
    id: str
    doc_id: str
    content: str
    chunk_index: int
    token_count: int


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: StoredChunk
    score: float
    document: StoredDocument


__all__ = ["DocumentInput", "RetrievedChunk", "StoredChunk", "StoredDocument"]
