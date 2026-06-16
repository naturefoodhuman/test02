<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-16 15:10:00
-->

# ADR-002: Dual-File Model Management System (A File + B File)

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director (per 4-Final Architecture Design v1.1.0)
- **Related**: 4-Final Architecture Design.md §5, 5-Architecture Upgrade Execution Plan (Wave 2)

## Context（背景）

Model selection in agent workflows needs to change frequently for different tasks, quality targets, cost budgets, and hardware constraints (especially on M1 Max 64GB unified memory).

Previously, model configuration was scattered across code, YAML parsing was handwritten and fragile, and switching models required code changes and restarts. This violated the goals of "one-line config switch" and long-term single-developer maintainability.

## Alternatives（备选方案）

- **A. Single unified config file**: Rejected. Mixes stable connection info with frequently changing routing decisions; hard to review and audit.
- **B. Pure code-based routing**: Rejected. Requires code changes for every model experiment; poor for non-engineers.
- **C. Dual-file separation**:
  - `config/models.yaml` (A file): All available models with connection details, capabilities, memory estimates, and data policy tags. Stable.
  - `config/routing_plans.yaml` (B file): Named plans that assign specific models to graph nodes, with execution mode (parallel/sequential), cost/time estimates, and `active_plan` switch.
- **D. LiteLLM-only config**: Rejected as sole source. We need human-readable, auditable, version-controllable plans that are independent of the gateway.

Selected: Dual-file system driven by `RoutingPlanEngine`.

## Decision（最终决策）

Adopt a strict dual-file model management system:

- `models.yaml` (A file) defines every usable model (local MTPLX/Ollama, Chinese APIs via LiteLLM, etc.). Includes `memory_required_gb`, `type`, `backend`, `data_policy`.
- `routing_plans.yaml` (B file) defines named plans (`default`, `high-quality`, `all-local`, `mtplx-hybrid`, etc.). Each plan maps node names to model keys from A file, plus execution semantics.
- Switching the active plan requires changing only the `active_plan` field in B file.
- `RoutingPlanEngine` performs startup cross-validation (every model referenced in B must exist in A).
- All code (LangGraph nodes, CLI, evaluator) obtains models exclusively through the engine — never hard-coded strings.

## Rationale（决策原因）

- Separation of concerns: A file is stable (infrastructure), B file is volatile (experimentation and policy).
- Enables data-driven optimization via `forge compare-plans` and MemoryStore.
- Supports GPU memory safety checks before parallel execution.
- Makes the system self-documenting and auditable.
- Directly supports the "HUB-SPOKE priority + multi-plan menu" principle in the final architecture.

## Consequences（影响）

**Positive**:
- Model experiments become trivial (edit one field).
- Clear audit trail of what model was used for which node in a given run.
- Enables safe parallel execution with memory pre-checks.
- Foundation for factory-level model matrix and cost control.

**Negative / Cost**:
- Requires strict validation at startup (good, but adds initial complexity).
- Two files to maintain per project (acceptable given the value).

## Risks（风险）

- Drift between A and B files (mitigated by mandatory `validate_consistency()` on every load).
- Over-proliferation of plans (mitigated by `enabled: false` for experimental ones and regular cleanup via privacy/plan audit commands).

## Rollback Strategy（回滚方案）

The dual-file system is now the SSOT. Any future change to model management must create a new ADR that supersedes this one. Old scattered config code has already been removed.

## Implementation Notes

- Pydantic models in `peer_review.config.schemas` enforce structure.
- `load_all_configs()` in loader.py performs cross-validation.
- `list_plans_summary()` and `check_parallel_memory_safety()` are first-class APIs.
- `mtplx-hybrid` plan was added in 2026-06-16 to align with real hardware usage.