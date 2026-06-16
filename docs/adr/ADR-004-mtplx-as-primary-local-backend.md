<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-16 15:10:00
-->

# ADR-004: MTPLX as Primary High-Performance Local Inference Backend

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director + real-machine validation
- **Related**: DEPLOYMENT_GUIDE.md, config/models.yaml (mtplx-* entries), routing_plans.yaml (mtplx-hybrid plan)

## Context（背景）

On M1 Max 64GB hardware, pure Ollama (even with MLX) showed limitations in speed and memory efficiency for large models (27B–35B class) under multi-node parallel review workloads. Real 8080/8082 MTPLX services demonstrated significantly better token throughput and memory behavior for the same quality level.

The pilot project (debt-collection peer review) is latency-sensitive when running A/B tests or multiple plans.

## Alternatives（备选方案）

- **A. Stay exclusively on Ollama + MLX**: Rejected for performance-critical paths after real benchmarks.
- **B. Use Llama.cpp / GGUF server (8084)**: Kept as secondary option (good for certain models), but not primary.
- **C. Make MTPLX (OpenAI-compatible high-performance server on 8080/8082) the default local backend for main brain and high-quality review nodes**: Selected, while keeping Ollama for lighter models and fallback.
- **D. Cloud-only for speed**: Rejected on privacy grounds for the core factory.

## Decision（最终决策）

Treat MTPLX-optimized models (Qwen3.6-27B-MTPLX, Gemma4-MTPLX, etc.) as first-class primary local inference engines for the factory.

- Define them in `config/models.yaml` with `provider: mtplx`, `backend: mtplx`, correct `base_url` (8080/8082), and accurate `memory_required_gb`.
- Create dedicated plans such as `mtplx-hybrid` that use MTPLX for primary + parallel reviewers.
- `llm_client.py` has a dedicated `MTPLXBackend` (OpenAI-compatible HTTP).
- Memory pre-checks in `RoutingPlanEngine` still apply.
- 8080/8082 services are considered part of the standard local deployment (see DEPLOYMENT_GUIDE).

Ollama remains supported for `local-fast`, embedding, and certain fallback scenarios.

## Rationale（决策原因）

- Measured real-world speed advantage on target hardware for the workloads we actually run (multi-expert legal review).
- OpenAI-compatible interface allows clean backend abstraction without forking the entire LLM calling layer.
- Enables the "high-quality local" plans that users actually want to run daily without API cost or data exfiltration.
- Aligns with the "Ollama + MLX + MTPLX + Llama.cpp" multi-backend reality documented in DEPLOYMENT_GUIDE.

## Consequences（影响）

**Positive**:
- Much better user experience for local-only high-quality reviews.
- Clear separation: MTPLX for heavy lifting, Ollama for light/fast/embedding.
- Still 100% local (no data leaves the machine).

**Negative / Cost**:
- Requires running additional MTPLX server processes (deployment complexity).
- Model files and server setup are hardware-specific (documented in DEPLOYMENT_GUIDE).

## Risks（风险）

- MTPLX server stability / memory leaks under long review sessions (mitigated by process restart discipline and monitoring in future).
- Inaccurate `memory_required_gb` estimates leading to OOM (mitigated by conservative values + 15% buffer in safety check).

## Rollback Strategy（回滚方案）

MTPLX entries can be disabled in plans (`enabled: false`) or removed from `models.yaml`. The abstraction in `llm_client.BackendFactory` makes it trivial to de-prioritize MTPLX later if a better local engine appears. No core logic depends on MTPLX being present.

## Implementation Notes

- `mtplx-hybrid` plan created 2026-06-16 and successfully executed end-to-end on real hardware.
- All LangGraph nodes automatically benefit once the plan is selected.