<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-16 15:25:00
-->

# FORGE Factory — Living Architecture Document (v1.1.0+)

**This is the Single Source of Truth (SSOT) for the current system architecture.**

- Last major update: 2026-06-16 (Phase 2 governance — B + C)
- All major decisions are backed by immutable ADRs in `docs/adr/` (7 core ADRs created in Phase 1)
- For historical decisions before full governance, see `docs/DECISIONS.md` (marked legacy)

## 1. Core Principles (from 4-Final Architecture Design v1.1.0)

- LangGraph 1.0 as the single graph orchestration engine (see ADR-001)
- Dual-file model management (A file = models.yaml, B file = routing_plans.yaml) (see ADR-002)
- Human-owned data policy via `privacy_policy.yaml` + enforcement (see ADR-003)
- Multi-backend local inference with MTPLX as primary high-performance path (see ADR-004)
- Pure LlamaIndex + ChromaDB for knowledge (no Agno dependency in new path) (see ADR-005)
- `forge eval` as official A/B testing tool (see ADR-006)
- `MemoryStore` + `ModelRunRecord` as the authoritative history for plans and RETRO (see ADR-007)

## 2. High-Level Layers (Current)

```
Core Layer (immutable methodology)
├── Five-stage workflow (DISCOVERY → SPEC → BUILD → HARDEN → RETRO)
└── Layered Decision Engine (Iron Gate + AI Reference + AI Generate)

Platform Layer (v1.1.0)
├── LangGraph 1.0 (graph/ + execution.py as canonical entry)
├── RoutingPlanEngine (dual-file driven)
├── DataPrivacyGate (policy file driven)
├── KnowledgeHub (pure LlamaIndex + ChromaDB)
├── DecisionEngine
├── MemoryStore (SQLite + ModelRunRecord)
└── LLM Client (multi-backend: MTPLX, Ollama, LiteLLM)

Factory Layer
├── forge CLI (eval, compare-plans, retro, new, etc.)
└── _factory/ (skills, patterns, experts, lessons)

Project Layer (pilot)
└── projects/debt-collection (压测沙包)
```

## 3. Key Components & Their Owners (SSOT)

- **Model & Plan Management**: `config/models.yaml` + `config/routing_plans.yaml` → `RoutingPlanEngine` (ADR-002)
- **Privacy**: `config/privacy_policy.yaml` → `DataPrivacyGate` (ADR-003)
- **Graph Execution**: `peer_review/graph/` (review_graph.py, nodes/, execution.py, state.py) — use `run_langgraph_review` (ADR-001)
- **Knowledge**: `peer_review/platform/knowledge_hub.py` (new pure implementation) (ADR-005)
- **Memory / Telemetry**: `peer_review/platform/memory_store.py` (ADR-007)
- **Legacy Agno code**: `orchestrator.py`, `knowledge_loader.py`, `agent_factory.py` — **Deprecated** (see ADR-001). Do not extend. Will be removed after stability window.

## 4. Important Files & Directories

- **Factory ADRs (immutable)**: `docs/adr/` (ADR-001 to ADR-007 + future)
- **Current Status**: `docs/PROJECT_STATE.md`
- **Governance Audit**: `DOCUMENT_AUDIT_REPORT.md`
- **Architecture Upgrade Completion**: `docs/UPGRADE_COMPLETION.md`
- **Handoff for Agents**: `HANDOFF.md` (always read first when joining)
- **Live Model Plans**: `config/routing_plans.yaml` (edit `active_plan` to switch)

## 5. Technology Choices (Current)

- Orchestration: LangGraph 1.0 (native)
- Local Inference: MTPLX (primary for heavy work) + Ollama (fast/embedding)
- RAG: LlamaIndex + ChromaDB (local embedding bge-m3 preferred)
- Config: Pydantic + YAML (dual file)
- Memory: SQLite (MemoryStore + LangGraph checkpointer)
- CLI: Click + Rich (forge + debt)

## 6. Evolution Rules

- Any change that affects architecture, core dependencies, workflows, or long-term maintainability **must** produce a new ADR in `docs/adr/`.
- Documentation must follow: Code → Tests → Documentation → CHANGELOG → ADR (if needed).
- Old Agno code path is frozen. New development must go through `graph/execution.py` and platform modules.

## 7. Quick Links

- All ADRs: `docs/adr/README.md`
- Model routing: `config/routing_plans.yaml` + `config/models.yaml`
- Real execution entry: `peer_review/graph/execution.py:run_langgraph_review`
- Governance framework: `DOCUMENT_AUDIT_REPORT.md`
- This living architecture doc: `docs/ARCHITECTURE.md`

## 8. Phase 2 & C Actions (2026-06-16)

- Created this living `ARCHITECTURE.md` as central SSOT (Phase 2).
- Strengthened cross-references from HANDOFF, README, PROJECT_STATE, etc. to `docs/adr/` and this file.
- **Deep old Agno legacy cleanup (C item)**: Added very strong deprecation blocks (with "严禁" rules, canonical path, and explicit removal date 2026-07-01 per ADR-001) to:
  - `_factory/patterns/peer-review/src/peer_review/orchestrator.py`
  - `knowledge_loader.py`
  - `agent_factory.py`
- **Traceability (C item)**: Added explicit "SSOT 引用" + ADR cross-references to 7+ core platform files (routing_plan_engine.py → ADR-002, knowledge_hub.py → ADR-005, memory_store.py → ADR-007, data_privacy_gate.py → ADR-003, decision_engine.py, graph/execution.py + review_graph.py → ADR-001, etc.).
- Reinforced R5 LLM file header rule in HANDOFF.md with clearer instructions for future agents.
- **Continuous Governance mechanism (C item)**: Created `scripts/governance_check.py` — a self-contained, regularly-runnable script that produces dated `docs/GOVERNANCE_CHECK_YYYY-MM-DD.md` (plus `GOVERNANCE_CHECK_LATEST.md`). It scans all 6 audit dimensions + R5 compliance + Agno footprint + cross-ref health. Run it after every significant change; always commit the generated report.
- Performed governance health check via the new script (zero active stale ZIP references; 7/7 ADRs have headers; R5 Python ~76/88 relevant files; 6 platform files back-link to ADRs).

---

**This document is a living document.** Update it whenever the architecture changes significantly. Always reference the corresponding ADR(s). When modifying this file or any governance-related file, add/update the LLM header at the very top per HANDOFF.md R5.