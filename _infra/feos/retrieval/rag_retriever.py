# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Placeholder RAG retriever wrapper; falls back by raising clear unavailable."""

from __future__ import annotations


class RAGRetrieverUnavailable(RuntimeError):
    pass


class RAGRetriever:
    def search(self, query: str, limit: int = 5):
        raise RAGRetrieverUnavailable("Local RAG adapter not wired yet; use lexical fallback")
