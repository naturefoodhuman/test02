# ADR-001: Immediate Full Migration to LangGraph 1.0 and Deprecation of Agno Abstraction Layer

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director (per 4-Final Architecture Design v1.1.0)
- **Related**: D-013 (early record), 4-Final Architecture Design.md §1.2 & ADR-001

## Context（背景）

The project initially used Agno (formerly phidata) for multi-agent orchestration in the peer-review pattern. By mid-2026, Agno had introduced multiple breaking changes within 6 months, making the API unstable and increasing maintenance cost dramatically.

The final target architecture (v1.1.0) explicitly requires:
- Native HUB-SPOKE support (parallel Send())
- Built-in checkpointer (SqliteSaver for HITL)
- Stable, community-backed graph API
- No unnecessary abstraction layers

Agno was becoming a root risk for long-term single-person maintainability.

## Alternatives（备选方案）

- **A. Keep Agno + build heavy abstraction layer (AgentRuntime)**: Rejected. Only defers the pain; adds complexity without solving instability.
- **B. Migrate to CrewAI or PydanticAI**: Rejected. Weaker native parallel (Send), less mature checkpointer/HITL support, smaller relevant community for complex legal workflows.
- **C. Stay on Agno and pin versions forever**: Rejected. Violates "long-term maintainable" and "Agent-Ready" principles.
- **D. Immediate direct use of LangGraph 1.0+ (langgraph>=1.0.10 + langgraph-checkpoint-sqlite>=3.0.1)**: Selected.

## Decision（最终决策）

Migrate the entire peer-review execution engine to native LangGraph 1.0 immediately (Phase A, line 1 of the Upgrade Plan).

- Remove reliance on Agno Team/Agent for the core review graph.
- Implement ReviewState (TypedDict with Annotated reducers for HUB-SPOKE).
- Use StateGraph + Send() for true parallel reviewer dispatch with information isolation.
- Use SqliteSaver for automatic checkpointing and human_review_gate interrupt.
- Keep a thin compatibility layer in orchestrator.py only during transition (to be deleted after 2-week stability window).

## Rationale（决策原因）

- LangGraph 1.0 provides explicit API stability commitment (critical for independent developer).
- Native support for exactly the three features we need most: HUB-SPOKE (Send), persistent checkpointer, and clean HITL.
- Large community (27k+ monthly searches) → better long-term support and examples.
- One-time migration cost is lower than the cumulative cost of fighting Agno breaking changes over 6–12 months.
- Aligns with the "no unnecessary abstraction" principle in the final architecture.

## Consequences（影响）

**Positive**:
- Stable foundation for all future multi-agent patterns.
- Real parallel execution (high-quality plan) and information-isolated sequential (all-local plan) become first-class.
- Easy to add streaming, memory, and human-in-the-loop later.
- Removes a major source of technical debt.

**Negative / Cost**:
- One-time migration effort (≈ 1–2 weeks for core path).
- Temporary dual implementation during transition.
- Need to rewrite node functions and state management.

## Risks（风险）

- LangGraph itself has a learning curve for the graph model (mitigated by incremental migration + tests).
- Potential subtle behavior differences in LLM calling / tool use during migration (mitigated by running full test suite after every sub-task).
- Old Agno code left behind could confuse future readers (mitigated by clear deprecation comments + scheduled deletion).

## Rollback Strategy（回滚方案）

- Keep the last known-good Agno-based implementation in a dedicated branch (`agno-backup`) for at least 2 weeks after LangGraph merge.
- All LangGraph changes are behind feature flags / separate entry points during transition.
- Full test suite (peer-review + debt-collection) acts as the safety net — any regression blocks merge.

## Implementation Notes

- New canonical entry: `peer_review.graph.execution.run_langgraph_review`
- debt CLI updated to prefer the new path.
- All platform components (RoutingPlanEngine, KnowledgeHub, DataPrivacyGate, DecisionEngine, MemoryStore) are framework-agnostic.
- Old Agno files (`orchestrator.py`, `knowledge_loader.py`, `agent_factory.py`) marked for deletion after stability period.

This decision is considered immutable historical record. Any future change must create a new superseding ADR.