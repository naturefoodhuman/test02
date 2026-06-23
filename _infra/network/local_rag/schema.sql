-- 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
-- 创建时间（北京时间）：2026-06-23 16:55:00

-- FORGE Network local RAG schema (E9-C1-S1-T1)
-- SQLite-first schema. Embeddings are stored as JSON text for portable tests.
-- sqlite-vec can be introduced later by adding a vec0 virtual table without
-- changing the RAGStore public API.

CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    source_url  TEXT NOT NULL,
    title       TEXT,
    raw_hash    TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    doc_id      TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(doc_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id   TEXT PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    embedding  TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_index USING fts5(
    chunk_id UNINDEXED,
    content,
    tokenize = 'unicode61'
);

CREATE TABLE IF NOT EXISTS access_log (
    id          TEXT PRIMARY KEY,
    chunk_id    TEXT NOT NULL,
    query       TEXT,
    accessed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_raw_hash ON documents(raw_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
