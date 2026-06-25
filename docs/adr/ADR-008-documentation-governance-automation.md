<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-25 00:00:00
-->

# ADR-008: Documentation Governance Automation as a Blocking Quality Gate

- **Status**: 已接受
- **Date**: 2026-06-25
- **Deciders**: User + Arena.ai Agent Mode
- **Related**: `DOCUMENT_AUDIT_REPORT.md`, `docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`, `scripts/governance_check.py`, `Makefile`

## Context（背景）

The project has repeatedly accumulated documentation drift: stale references, unclear SSOT, historical documents being mistaken for current truth, missing or delayed changelog entries, and manual R5 header enforcement. The original `DOCUMENT_AUDIT_REPORT.md` identified documentation governance as a major maintainability risk.

As the factory is intended to be operated by both humans and future agents, documentation governance must be automated and regularly enforced rather than relying on manual discipline.

## Decision（决策）

Make documentation governance a first-class blocking quality gate.

The canonical automation entry points are:

```bash
make docs-check
make governance-check
python3 scripts/governance_check.py --strict
```

The governance checker must cover at least:

1. changed-files R5 header check;
2. `TASK_BACKLOG.md` ↔ `docs/DEV_LOG.md` synchronization check;
3. code/config/script changes requiring `docs/CHANGELOG.md` updates;
4. architecture-sensitive trigger detection with ADR review prompt;
5. automatic generation of `docs/DOCUMENT_INDEX.md`;
6. core SSOT existence checks;
7. current onboarding/core docs link checks;
8. stale active ZIP / `_patches` process references;
9. legacy Agno bad import checks.

## Rationale（理由）

- The factory's value depends on being agent-ready and handoff-safe.
- Manual governance was repeatedly insufficient.
- A lightweight local script avoids introducing new infrastructure while still enabling strict checks.
- `DOCUMENT_INDEX.md` gives humans and agents a live map of current / reference / governance / training documents.
- Trigger-based ADR prompts reduce the chance of silently changing architecture or workflow policy without a decision record.

## Consequences（影响）

Positive:

- Every development turn can run a repeatable governance gate.
- New or modified files are checked for R5 headers.
- Code changes cannot silently skip changelog updates.
- Backlog status changes cannot silently skip development log updates.
- Current core docs are checked for broken links.
- Future agents have a generated document index.

Negative / Cost:

- Running governance check mutates generated files (`GOVERNANCE_CHECK_*`, `DOCUMENT_INDEX.md`), so agents must remember to commit those outputs when appropriate.
- Architecture trigger detection is heuristic and may produce false-positive warnings.
- Historical R5 compliance remains below 100%; changed-files checks are used to prevent new debt rather than forcing immediate mass rewrites.

## Implementation Notes

Implemented on 2026-06-25:

- `scripts/governance_check.py --strict`
- `make docs-check`
- `make governance-check`
- generated `docs/DOCUMENT_INDEX.md`
- generated `docs/GOVERNANCE_CHECK_2026-06-25.md`

## Rollback Strategy（回滚方案）

If the strict gate blocks legitimate emergency work, it can be run without `--strict` to generate warnings only. However, any bypass must be documented in `docs/DEV_LOG.md` and corrected before the next normal commit.
