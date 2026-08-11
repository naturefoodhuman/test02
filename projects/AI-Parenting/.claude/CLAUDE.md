# CLAUDE.md — AI Parenting Project Instructions

> Scope: This file applies only to `projects/AI-Parenting/`.
> This project is isolated from `projects/AI-Parenting-Copilot/`.

---

## 1. Project Identity

- Project root: `projects/AI-Parenting/`
- This is the active AI Parenting implementation path.
- Do not use `projects/AI-Parenting-Copilot/` as implementation source unless the user explicitly says so.
- Do not modify `projects/AI-Parenting-Copilot/`.

---

## 2. Required Read Order for New Sessions

At the start of a new session, read:

1. `docs/HANDOFF.md`
2. `docs/PROJECT_STATE.md`
3. `docs/TASK_BACKLOG.md`
4. `docs/ARCHITECTURE_FINAL.md`
5. `docs/ENGINEERING_DESIGN.md`
6. Latest section of `docs/DEV_LOG.md`
7. Latest section of `docs/CHANGELOG.md`
8. Relevant `docs/ADR/*.md`

After reading, output:

- Current milestone
- Current in-progress task
- Last completed task
- Next proposed task
- Files likely to change
- Tests to run
- Any required user confirmation

Do not start coding before this summary unless the user explicitly asks for immediate implementation.

---

## 3. Source of Truth

- Current status SSOT: `docs/PROJECT_STATE.md`
- Task status SSOT: `docs/TASK_BACKLOG.md`
- Architecture SSOT: `docs/ARCHITECTURE_FINAL.md`
- Engineering implementation baseline: `docs/ENGINEERING_DESIGN.md`
- Development history: `docs/DEV_LOG.md`
- Change history: `docs/CHANGELOG.md`
- Architecture changes: `docs/ADR/*.md`

Do not create `docs/SESSION_STATE.md`; `docs/PROJECT_STATE.md` already serves that role.

---

## 4. Boundary Rules

- Do not edit `projects/AI-Parenting-Copilot/`.
- Do not write this project’s state into the factory root docs.
- Do not copy implementation from `AI-Parenting-Copilot` unless the user explicitly approves.
- Do not commit real secrets, `.env`, `.env_*`, `.env-*`, or local runtime files.

---

## 5. Architecture Rules

Follow these rules from the project architecture:

1. Local-first by default.
2. Rule Engine owns medical dosage and threshold decisions.
3. LLM must not freely calculate medication dosage.
4. Privacy Gateway owns cloud-bound redaction.
5. Mutating operations must be audit logged.
6. Red/orange alerts require delivery guarantees.
7. Factory capabilities should be reused through adapters, not copied.
8. Architecture boundary changes require ADR before implementation.

---

## 6. Development Workflow

For each task:

1. Confirm task ID from `docs/TASK_BACKLOG.md`.
2. Inspect relevant architecture/design docs.
3. Implement minimal vertical slice.
4. Add or update tests.
5. Run project checks.
6. Update:
   - `docs/PROJECT_STATE.md`
   - `docs/TASK_BACKLOG.md`
   - `docs/DEV_LOG.md`
   - `docs/CHANGELOG.md`   
7. Commit only intentional changes.

---

## 7. Commands

Common commands:

```bash
   cd projects/AI-Parenting

   make lint
   make typecheck
   make test
   make docs-check
   make governance-check

   make infra-up
   make db-migrate
   make db-seed
   make run-dev

Prefer existing Make targets over ad hoc commands.

---

## 8. Python Tooling

1. Use Python 3.11+.
2. Prefer uv / uv pip.
3. Do not use plain pip install as the first recommendation.
4. Keep ruff and mypy clean unless the user explicitly accepts a temporary exception.

---

## 9. Logging and Memory Discipline

When finishing a task, update project docs before ending the session.

docs/DEV_LOG.md should include:

   - Task ID
   - What changed
   - Why
   - Files touched
   - Tests run
   - Known limitations
   - Next step

docs/CHANGELOG.md should include:

   - User-visible changes
   - Behavior changes
   - Schema/API changes
   - Migration notes if any

---

## 10. Compact Instructions

When compacting or summarizing this project, preserve:

   - Current milestone and active APC task
   - Architecture decisions and ADR status
   - Database schema and migration state
   - API contracts
   - Test counts and failing tests
   - Privacy / Rule Engine / Audit constraints
   - Next concrete task and required commands

Do not preserve long raw logs unless they contain an unresolved error.