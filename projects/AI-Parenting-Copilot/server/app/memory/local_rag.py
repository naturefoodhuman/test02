# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 22:50:00

"""M5 Local RAG adapter for memory correction snippets.

The project does not copy the factory Local RAG implementation. This adapter accepts
an injected factory RAG store (or any compatible test double) and normalizes returned
chunks into a small, privacy-aware structure for Copilot context.
"""

from __future__ import annotations

from typing import Any


class LocalRAGMemoryAdapter:
    """Thin adapter around factory `_infra.network.local_rag.RAGStore` search."""

    def __init__(self, store: object | None = None) -> None:
        self.store = store

    def available(self) -> bool:
        return self.store is not None and callable(getattr(self.store, "search", None))

    def search_corrections(self, query: str, *, limit: int = 5) -> list[dict[str, object]]:
        search = getattr(self.store, "search", None)
        if not callable(search):
            return []
        try:
            results = search(query, top_k=limit)
        except TypeError:
            results = search(query, limit)
        return [self._to_context_item(item) for item in list(results)[:limit]]

    @staticmethod
    def _to_context_item(item: Any) -> dict[str, object]:
        chunk = getattr(item, "chunk", None)
        document = getattr(item, "document", None)
        return {
            "content": str(getattr(chunk, "content", "")),
            "score": float(getattr(item, "score", 0.0) or 0.0),
            "source_url": str(getattr(document, "source_url", "")),
            "title": getattr(document, "title", None),
        }
