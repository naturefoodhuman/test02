# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

"""Unit tests for Local RAG (E9-C1/C2/C3/C4)."""

import sqlite3

import pytest

from _infra.network.local_rag import BGE_M3_Embedder, DocumentInput, RAGStore, init_rag_db


class FakeEmbedClient:
    def __init__(self):
        self.calls = []

    def embeddings(self, model, prompt, **kwargs):
        self.calls.append((model, prompt))
        vec = [0.0] * 8
        lower = prompt.lower()
        if "alpha" in lower:
            vec[0] = 1.0
        elif "beta" in lower:
            vec[1] = 1.0
        else:
            vec[2] = 1.0
        return {"embedding": vec}


def test_init_rag_db_creates_schema(tmp_path):
    db = init_rag_db(tmp_path / "rag.db")
    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','virtual')")}

    assert "documents" in tables
    assert "chunks" in tables
    assert "embeddings" in tables
    assert "fts_index" in tables
    assert "access_log" in tables


def test_embedder_uses_cache():
    client = FakeEmbedClient()
    embedder = BGE_M3_Embedder(client=client, expected_dim=8)

    first = embedder.embed("alpha text")
    second = embedder.embed("alpha text")

    assert first == second
    assert len(client.calls) == 1


def test_embedder_rejects_wrong_dimension():
    class BadClient:
        def embeddings(self, model, prompt, **kwargs):
            return {"embedding": [1.0, 2.0]}

    embedder = BGE_M3_Embedder(client=BadClient(), expected_dim=8)

    with pytest.raises(ValueError):
        embedder.embed("bad")


def test_rag_store_add_document_and_chunks(tmp_path):
    store = RAGStore(tmp_path / "rag.db", embedder=BGE_M3_Embedder(client=FakeEmbedClient(), expected_dim=8), chunk_size_tokens=3, chunk_overlap_tokens=1)
    doc = store.add_document(DocumentInput(source_url="https://example.com/a", title="A", content="alpha one two three four"))

    loaded = store.get_document(doc.id)
    chunks = store.list_chunks(doc.id)

    assert loaded == doc
    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0


def test_rag_store_dedup_by_raw_hash(tmp_path):
    store = RAGStore(tmp_path / "rag.db", embedder=BGE_M3_Embedder(client=FakeEmbedClient(), expected_dim=8))
    first = store.add_document(DocumentInput(source_url="https://example.com/a", content="alpha"))
    second = store.add_document(DocumentInput(source_url="https://example.com/b", content="alpha"))

    assert first.id == second.id


def test_rag_store_search_returns_top_k_and_logs_access(tmp_path):
    store = RAGStore(tmp_path / "rag.db", embedder=BGE_M3_Embedder(client=FakeEmbedClient(), expected_dim=8))
    alpha = store.add_document(DocumentInput(source_url="https://example.com/alpha", title="Alpha", content="alpha topic"))
    beta = store.add_document(DocumentInput(source_url="https://example.com/beta", title="Beta", content="beta topic"))

    results = store.search("alpha query", top_k=1)

    assert len(results) == 1
    assert results[0].document.id == alpha.id
    assert results[0].score > 0.9
    with sqlite3.connect(tmp_path / "rag.db") as conn:
        count = conn.execute("SELECT COUNT(*) FROM access_log").fetchone()[0]
    assert count == 1
