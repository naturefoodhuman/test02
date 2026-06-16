# ADR-007: MemoryStore + ModelRunRecord as Authoritative Source for Plan Comparison and RETRO Data

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director
- **Related**: 4-Final Architecture Design §2.2 (MemoryStore), §3.5 (RETRO), MemoryStore platform module, forge compare-plans / retro

## Context（背景）

After every peer-review run (whether via `debt review` or `forge eval`), we need persistent, queryable records of:
- Which plan was used
- Which models actually ran on which nodes
- Total time and estimated cost
- Divergence score
- (Future) human quality score and adoption

This data is essential for `forge compare-plans`, automatic RETRO data collection, and long-term "which scheme is actually best for this domain" learning.

Scattered logs or in-memory state are insufficient.

## Alternatives（备选方案）

- **A. Log files + manual parsing**: Rejected. Not queryable, easy to lose.
- **B. External observability (LangSmith, etc.)**: Rejected on data exfiltration and cost grounds for an independent developer tool.
- **C. Dedicated SQLite store (`runtime/memory.db`) with `ModelRunRecord` Pydantic model**:
  - Written automatically at the end of every successful review.
  - Provides `get_plan_comparison(days)` and plan-level aggregates.
  - Used by both CLI commands and RETRO generation.
- Selected: C.

## Decision（最终决策）

`MemoryStore` (backed by `runtime/memory.db`) + `ModelRunRecord` is the Single Source of Truth for historical execution data used in plan comparison and factory retrospectives.

- Every completed LangGraph review (via the official `run_langgraph_review` path) must call `memory.record_run(...)`.
- The store is project-root aware and lives outside Git (in `.gitignore`).
- Schema includes `plan_id`, `models_used`, `total_time_seconds`, `total_cost_usd`, `divergence_score`, optional human fields.
- `forge compare-plans` and `forge retro` are the primary consumers.

## Rationale（决策原因）

- Enables the "model scheme effect recording" and "RETRO additional collection" requirements in the final architecture.
- Provides the data foundation for future automatic plan recommendation.
- Simple, local, auditable, zero external dependency.
- Naturally feeds the five-stage workflow's RETRO phase.

## Consequences（影响）

**Positive**:
- Objective history of every experiment and production review.
- Powers both interactive comparison and automated experience extraction.
- Easy to extend with new fields (human_quality_score, adopted_by_user, etc.).

**Negative / Cost**:
- Requires explicit recording call at the end of every review path (small but mandatory).
- Database can grow; retention policy may be needed later.

## Risks（风险）

- Human quality scores remain optional → comparison may be biased toward speed/cost (documented; indirect signals like divergence and adoption rate are used as fallback).
- Multiple processes writing concurrently (mitigated by SQLite WAL mode and simple locking in practice).

## Rollback Strategy（回滚方案）

The store is additive. Old runs can be ignored or the DB deleted (data loss is acceptable for this non-critical telemetry). The recording logic can be made optional via a flag if needed in the future, but the default must remain "record everything".

## Implementation Notes

- `MemoryStore` lives in `peer_review.platform.memory_store`.
- Automatically called from `debt/cli.py` (real review) and indirectly benefits from `forge eval` (via the review path).
- Visible in real runs: "📝 已记录运行结果至 MemoryStore (耗时: 241s, 成本: $0.0000)".
- Queried by `forge compare-plans` and `forge retro generate`.