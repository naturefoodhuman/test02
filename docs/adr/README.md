<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-25 00:00:00
-->

# Factory-Level Architecture Decision Records (ADRs)

This directory is the **Single Source of Truth** for all major architectural and governance decisions in the FORGE Factory (root level, not per-project).

## Purpose

Per the Documentation Governance framework (see `DOCUMENT_AUDIT_REPORT.md`):

- Every significant architecture, technology, workflow, or policy decision must have a corresponding ADR.
- ADRs are **immutable historical records**. They are never deleted.
- Only marking as `Superseded` or `Deprecated` is allowed.
- New decisions create new ADRs that may supersede older ones.

## Current ADRs (v1.1.0 Core Architecture)

| ADR | Title | Status | Date | Key Impact |
|-----|-------|--------|------|------------|
| [ADR-001](ADR-001-langgraph-migration.md) | Immediate Full Migration to LangGraph 1.0 | 已接受 | 2026-06-16 | Core execution engine, removal of Agno for graphs |
| [ADR-002](ADR-002-dual-file-model-management.md) | Dual-File Model Management (A + B files) | 已接受 | 2026-06-16 | `models.yaml` + `routing_plans.yaml`, RoutingPlanEngine |
| [ADR-003](ADR-003-data-privacy-gate-and-policy-file.md) | Data Outbound Control via privacy_policy.yaml + DataPrivacyGate | 已接受 | 2026-06-16 | Privacy enforcement, human_approve gates |
| [ADR-004](ADR-004-mtplx-as-primary-local-backend.md) | MTPLX as Primary High-Performance Local Inference Backend | 已接受 | 2026-06-16 | 8080/8082 MTPLX as first-class local engine |
| [ADR-005](ADR-005-knowledgehub-pure-llamaindex-chromadb.md) | Pure LlamaIndex + ChromaDB for KnowledgeHub | 已接受 | 2026-06-16 | De-dupe, version control, local embedding (post-Agono) |
| [ADR-006](ADR-006-forge-eval-as-ab-testing-capability.md) | forge eval as Core Factory A/B Testing Tool | 已接受 | 2026-06-16 | Real plan comparison, gold dataset, MemoryStore integration |
| [ADR-007](ADR-007-memorystore-as-plan-comparison-ssot.md) | MemoryStore + ModelRunRecord as SSOT for Plan Comparison & RETRO | 已接受 | 2026-06-16 | Historical execution data for compare-plans and retro |
| [ADR-008](ADR-008-documentation-governance-automation.md) | Documentation Governance Automation as a Blocking Quality Gate | 已接受 | 2026-06-25 | `make docs-check`, governance automation, document index |
| [ADR-009](ADR-009-local-model-runtime-configuration.md) | Local Model Runtime Configuration as SSOT | 已接受 | 2026-06-26 | `config/model_runtime.yaml`, runtime tuning, MTP flags |

## How to Read

- Start with the most recent ADRs for the current state of the system.
- Cross-reference with:
  - `docs/DECISIONS.md` (summary / legacy early decisions)
  - `DOCUMENT_AUDIT_REPORT.md` (governance context)
  - `docs/UPGRADE_COMPLETION.md` (overall upgrade status)
  - `config/routing_plans.yaml` + `config/models.yaml` (live implementation of ADR-002)

## Process

Any engineer or Agent making a change that affects architecture, core dependencies, workflows, or long-term maintainability **must** create a new ADR in this directory before merging.

See `DOCUMENT_AUDIT_REPORT.md` → "ADR Rules" and "Continuous Governance" for enforcement details.

---

**Last updated**: 2026-06-26 (ADR-009 Local Model Runtime Configuration)