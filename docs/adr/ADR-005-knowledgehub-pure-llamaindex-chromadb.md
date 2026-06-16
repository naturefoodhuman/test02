<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-16 15:10:00
-->

# ADR-005: Pure LlamaIndex + ChromaDB Implementation for KnowledgeHub (Removal of Agno Dependency)

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director (post LangGraph migration)
- **Related**: ADR-001 (LangGraph), old KnowledgeLoader in orchestrator.py / knowledge_loader.py

## Context（背景）

The original KnowledgeHub / KnowledgeLoader relied on Agno's `ChromaDb` and `AgentKnowledge` wrappers. After the decision to migrate the execution engine to native LangGraph (ADR-001), continuing to depend on Agno just for RAG created an unnecessary and inconsistent dependency.

Real usage showed the need for explicit version-based de-duplication (VERSION file + collection metadata), better control over embedding model (local bge-m3 via Ollama), and clean separation from the old agent framework.

## Alternatives（备选方案）

- **A. Keep using Agno's vector wrappers**: Rejected. Creates mixed dependency after the core engine has moved on; harder to reason about and upgrade.
- **B. Direct ChromaDB + custom code**: Rejected. Loses the mature document loading, chunking, and retrieval abstractions that LlamaIndex provides.
- **C. Pure LlamaIndex + ChromaVectorStore + PersistentClient**:
  - Use `llama_index.vector_stores.chroma`
  - Use `SimpleDirectoryReader` for loading expert knowledge directories
  - Implement our own version hash + collection metadata de-dupe logic
  - Use OllamaEmbedding (bge-m3) for local consistency
- Selected: C.

## Decision（最终决策）

Re-implement `KnowledgeHub` (and deprecate old `knowledge_loader.py`) as a thin, pure LlamaIndex + ChromaDB layer:

- No Agno imports in the new path.
- Explicit `load_expert_knowledge(expert_id)` with version check.
- `search(expert_id, query, top_k)` returns clean text snippets.
- Embedding is configurable but defaults to local Ollama bge-m3.
- Version is computed from file mtime+size hash and stored in Chroma collection metadata.
- Old Agno-based loader remains only for backward compatibility during transition.

## Rationale（决策原因）

- Consistency with the "LangGraph native + minimal framework surface" philosophy.
- Full control over embedding model and retrieval (critical for legal accuracy).
- Simpler dependency tree for long-term maintenance.
- Enables future RAG quality monitoring and hybrid retrieval without fighting Agno abstractions.

## Consequences（影响）

**Positive**:
- Clean dependency graph.
- Better version de-duplication and "reuse cache" logging visible to users.
- Easier to swap embedding backends later (e.g., add local reranker).

**Negative / Cost**:
- One-time re-implementation of the loader (completed 2026-06-16).
- Need to ensure LlamaIndex embedding dependencies are installed (ollama-embeddings or huggingface).

## Risks（风险）

- LlamaIndex embedding package resolution issues (seen in early runs; mitigated by explicit `llama-index-embeddings-ollama`).
- Collection name collisions during migration (handled by delete-on-rebuild logic).

## Rollback Strategy（回滚方案）

The new `KnowledgeHub` is the canonical implementation. Old Agno loader files are marked deprecated. If a superior RAG abstraction appears, a new ADR will be created. The interface (`load_expert_knowledge`, `search`, `inject_skill`) is intentionally small and stable.

## Implementation Notes

- New implementation lives in `peer_review.platform.knowledge_hub`.
- Used by `primary_expert` node and `run_langgraph_review`.
- Version computation and "📦 复用专家 ... 知识库缓存" / "📚 正在构建..." logs are now consistent and visible in real runs (e.g., mtplx-hybrid eval).