# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Optional adapter to existing _infra.network Local RAG."""

from __future__ import annotations


class LocalRAGAdapter:
    def __init__(self, store=None):
        self.store = store

    def available(self) -> bool:
        return self.store is not None

    def search_similar(self, query: str, limit: int = 5):
        if not self.store:
            return []
        if hasattr(self.store, "search"):
            return self.store.search(query, limit=limit)
        return []
