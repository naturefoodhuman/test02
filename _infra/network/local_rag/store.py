# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:55:00

"""SQLite local RAG store with Python KNN fallback (E9-C3/E9-C4)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sqlite3
from typing import Iterable, Mapping
import uuid

from .embedder import BGE_M3_Embedder
from .models import DocumentInput, RetrievedChunk, StoredChunk, StoredDocument

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def init_rag_db(db_path: str | Path = "runtime/rag.db") -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    return path


class RAGStore:
    def __init__(
        self,
        db_path: str | Path = "runtime/rag.db",
        embedder: BGE_M3_Embedder | None = None,
        chunk_size_tokens: int = 512,
        chunk_overlap_tokens: int = 50,
    ):
        self.db_path = init_rag_db(db_path)
        self.embedder = embedder or BGE_M3_Embedder()
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def raw_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def chunk(self, text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
        size = size or self.chunk_size_tokens
        overlap = overlap if overlap is not None else self.chunk_overlap_tokens
        words = text.split()
        if not words:
            return []
        if len(words) <= size:
            return [text]
        chunks = []
        step = max(1, size - overlap)
        for start in range(0, len(words), step):
            part = words[start : start + size]
            if part:
                chunks.append(" ".join(part))
            if start + size >= len(words):
                break
        return chunks

    def add_document(self, doc: DocumentInput) -> StoredDocument:
        raw_hash = self.raw_hash(doc.content)
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM documents WHERE raw_hash = ?", (raw_hash,)).fetchone()
            if existing:
                return StoredDocument(existing["id"], existing["source_url"], existing["title"], existing["raw_hash"])

            doc_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO documents (id, source_url, title, raw_hash, metadata) VALUES (?, ?, ?, ?, ?)",
                (doc_id, doc.source_url, doc.title, raw_hash, json.dumps(dict(doc.metadata), ensure_ascii=False)),
            )
            chunks = self.chunk(doc.content)
            for index, content in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                token_count = len(content.split())
                conn.execute(
                    "INSERT INTO chunks (id, doc_id, content, chunk_index, token_count) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, doc_id, content, index, token_count),
                )
                embedding = self.embedder.embed(content)
                conn.execute(
                    "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
                    (chunk_id, json.dumps(embedding, separators=(",", ":"))),
                )
                conn.execute("INSERT INTO fts_index (chunk_id, content) VALUES (?, ?)", (chunk_id, content))
            conn.commit()
            return StoredDocument(doc_id, doc.source_url, doc.title, raw_hash)

    def get_document(self, doc_id: str) -> StoredDocument | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            return None
        return StoredDocument(row["id"], row["source_url"], row["title"], row["raw_hash"])

    def list_chunks(self, doc_id: str) -> list[StoredChunk]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index", (doc_id,)).fetchall()
        return [StoredChunk(r["id"], r["doc_id"], r["content"], r["chunk_index"], r["token_count"]) for r in rows]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        query_embedding = self.embedder.embed(query)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.id AS chunk_id, c.doc_id, c.content, c.chunk_index, c.token_count,
                       e.embedding, d.source_url, d.title, d.raw_hash
                FROM chunks c
                JOIN embeddings e ON e.chunk_id = c.id
                JOIN documents d ON d.id = c.doc_id
                """
            ).fetchall()

        results = []
        for row in rows:
            embedding = [float(x) for x in json.loads(row["embedding"])]
            score = self._cosine(query_embedding, embedding)
            chunk = StoredChunk(row["chunk_id"], row["doc_id"], row["content"], row["chunk_index"], row["token_count"])
            doc = StoredDocument(row["doc_id"], row["source_url"], row["title"], row["raw_hash"])
            results.append(RetrievedChunk(chunk=chunk, score=score, document=doc))

        results.sort(key=lambda item: item.score, reverse=True)
        top = results[:top_k]
        with self._connect() as conn:
            for item in top:
                conn.execute(
                    "INSERT INTO access_log (id, chunk_id, query) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), item.chunk.id, query),
                )
            conn.commit()
        return top


__all__ = ["RAGStore", "init_rag_db"]
