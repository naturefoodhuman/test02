# ADR-003: Data Outbound Control via privacy_policy.yaml + DataPrivacyGate

- **Status**: 已接受
- **Date**: 2026-06-16
- **Deciders**: Architecture Transformation Director (per 4-Final Architecture Design v1.1.0)
- **Related**: 4-Final Architecture Design.md §6.3, Upgrade Plan CAP-4.1, Wave 4

## Context（背景）

Legal and sensitive case data (debtor name, ID number, amount, evidence) must never leave the user's machine without explicit human intent and policy control. Hard-coding "what can go out" in Python is brittle, non-auditable, and places policy decisions on the engineer instead of the data owner.

Chinese API usage (DeepSeek, Qwen, GLM) is common for quality but triggers data-residency and privacy concerns.

## Alternatives（备选方案）

- **A. Hard-code sensitivity rules in code**: Rejected. Not auditable, not changeable by non-engineers, violates "human defines policy" principle.
- **B. Per-call confirmation without policy file**: Rejected. Too noisy and inconsistent.
- **C. Strategy file + enforcement engine**:
  - `privacy_policy.yaml`: Human-owned file declaring field-level policies (`local_only`, `human_approve`, `mask_then_allow`, `allow`) and endpoint rules.
  - `DataPrivacyGate`: Pure executor that reads the policy and either blocks, requires explicit "yes", or allows (with optional masking).
- **D. External policy service**: Rejected for single-developer offline use.

Selected: C.

## Decision（最终决策）

Introduce a policy-file-driven data outbound control system:

- `config/privacy_policy.yaml` is the single source of truth for what data may leave and under what conditions.
- Four policy types only: `local_only`, `human_approve`, `mask_then_allow`, `allow`.
- `DataPrivacyGate.check()` is called at CLI entry for API plans and at node level inside LangGraph (via `llm_client.chat` privacy_context).
- Human approval requires explicit lowercase `yes` (no y/enter shortcuts).
- All approvals and blocks are logged (audit trail).
- Default for undefined fields is conservative (`human_approve`).

## Rationale（决策原因）

- Policy belongs to the human owner, not the code.
- File format is simple enough for quarterly manual review (`forge privacy-audit`).
- Technical enforcement layer makes bypass impossible (unlike process-only gates).
- Directly supports "data out-bound strategy fileization" key decision in the final architecture.
- Enables safe use of Chinese APIs while keeping highest-risk fields (real name, ID) local-only.

## Consequences（影响）

**Positive**:
- Clear, auditable privacy posture.
- Non-engineers can adjust policy without touching code.
- Automatic blocking of `local_only` fields even if someone tries to call an API node.
- Foundation for future cross-project policy inheritance.

**Negative / Cost**:
- Every new sensitive field requires a policy entry (acceptable discipline).
- Slight friction on first API plan use (human confirmation).

## Risks（风险）

- Policy sprawl (too many fields) → mitigated by quarterly audit command and "keep it simple" guidance in the file header.
- Masking rules become insufficient over time → policy file is versioned and human-reviewed.

## Rollback Strategy（回滚方案）

The `privacy_policy.yaml` + `DataPrivacyGate` pair is now the enforced mechanism. Any relaxation must be done by editing the policy file (with CHANGELOG + optional new ADR for major policy philosophy changes). Code-level bypasses are forbidden.

## Implementation Notes

- Enforced in `debt/cli.py` before graph start and inside `llm_client._privacy_check`.
- Four policy verbs are the only ones allowed in the schema.
- `request_human_approval` is strict and logs every decision.