# ADR-006: forge eval as Core Factory A/B Testing and Model Suitability Tool

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director + real-machine validation
- **Related**: 4-Final Architecture Design §3.2 (forge compare-plans), evaluator.py, gold_dataset.json

## Context（背景）

To make data-driven model and plan selection possible, the factory needs a repeatable way to run the same gold cases against different routing plans (`default`, `high-quality`, `all-local`, `mtplx-hybrid`, etc.), collect latency, TPS, quality signals, divergence, and cost, then store the results for later analysis (`forge compare-plans`).

Manual ad-hoc runs are not reproducible and do not feed the MemoryStore / RETRO loop.

## Alternatives（备选方案）

- **A. Rely only on real `debt review` runs + manual note-taking**: Rejected. Too slow and non-repeatable for A/B experiments.
- **B. External benchmarking tool**: Rejected. Would duplicate the exact LangGraph + platform stack we already have.
- **C. Built-in `forge eval --plans <list>` command**:
  - Loads a gold dataset (`_factory/evals/gold_dataset.json`)
  - Executes full real `run_langgraph_review` for each plan
  - Computes simple quality heuristics against expected_logic
  - Records timing, models used, divergence
  - Outputs table + saves JSON report
- Selected: C (with future evolution toward human quality scores).

## Decision（最终决策）

Make `forge eval` a first-class, officially supported factory capability for A/B testing routing plans and model suitability.

- It must run **real** LangGraph + **real** LLM calls (no simulation after 2026-06-16 fixes).
- It must respect the current `active_plan` or accept `--plans` override via `RoutingPlanEngine.set_active_plan`.
- Results feed MemoryStore (via the review path) and can be queried by `forge compare-plans`.
- Gold dataset cases are treated as the canonical evaluation set for the debt domain.

## Rationale（决策原因）

- Directly supports the "scheme comparison data" and "data-driven model selection" goals in the final architecture.
- Enables rapid validation of new plans (e.g., mtplx-hybrid) before recommending them to users.
- Provides objective numbers (time, divergence) even when human quality scoring is optional.
- Closes the loop between experimentation and RETRO / factory knowledge.

## Consequences（影响）

**Positive**:
- Reproducible experiments.
- Objective basis for choosing default plan or hardware-specific plans.
- Natural integration with existing MemoryStore and report generation.

**Negative / Cost**:
- Running full eval on large gold sets with heavy local models is time-consuming (expected and documented).
- Quality scoring is currently heuristic-based (future work: integrate human scoring or lightweight RAGAS-style metrics).

## Risks（风险）

- Gold dataset becoming stale relative to real case distribution (mitigated by periodic human review of cases).
- Over-reliance on automated scores without human validation (explicitly warned in docs and evaluator output).

## Rollback Strategy（回滚方案）

The command can be disabled or the gold dataset emptied if the approach proves ineffective. The underlying `run_langgraph_review` path remains the real execution engine regardless.

## Implementation Notes

- Fixed in 2026-06-16 to use real `graph.invoke` + real MTPLX calls.
- Successfully executed 5-case `mtplx-hybrid` run on real hardware with correct model attribution and MemoryStore recording.
- Report saved to `runtime/model_eval_report.json`.