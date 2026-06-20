<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-06-20 22:20:00 CST
-->

# Repository Cleanup Report

## Summary

| Metric | Count | Notes |
|---|---:|---|
| Scanned tracked files | 326 | Based on revised git index. |
| Active retained tracked files | 326 | `_obsolete/` is no longer tracked. |
| Tracked `_obsolete/` files | 0 | Required by user: `_obsolete/` ignored, not pushed. |
| Existing `_obsolete/` files removed from Git index | 15 | Local copies retained under ignored `_obsolete/`. |
| Active files archived locally and removed from GitHub surface | 6 | One-off scripts/log only; local copies retained. |
| User-requested folders restored | 3 | `projects/legal-bot/`, `projects/project-b/`, `retro-data-share/`. |

## User-requested Restoration

These folders were restored and remain tracked/active:

- `projects/legal-bot/`
- `projects/project-b/`
- `retro-data-share/`

## Obsolete / Local-only Assets

Because `_obsolete/` must be ignored and not pushed, obsolete assets are now local-only archives.

| Original Path | Local Archive Path | Reason |
|---|---|---|
| `forge_diagnose_20260620_152026.log` | `_obsolete/forge_diagnose_20260620_152026.log` | Runtime diagnostic log; local-only archive because `_obsolete/` is ignored. |
| `scripts/demo_knowledge_pipeline.py` | `_obsolete/scripts/demo_knowledge_pipeline.py` | Standalone demo/PoC script with no active SOP references. |
| `scripts/e2e_review_test.py` | `_obsolete/scripts/e2e_review_test.py` | Historical validation script using retired orchestrator import path; canonical tests remain under peer-review tests. |
| `scripts/fix-claude-code.sh` | `_obsolete/scripts/fix-claude-code.sh` | One-off local machine repair script mutating home-directory config and using absolute Mac path. |
| `scripts/test_model_direct.py` | `_obsolete/scripts/test_model_direct.py` | One-off local-port/direct-model diagnostic with absolute Mac path. |
| `scripts/verify_on_demand_fix.py` | `_obsolete/scripts/verify_on_demand_fix.py` | One-off on-demand-load diagnostic with local ports/process killing. |

Existing tracked `_obsolete/` files were removed from the Git index. They remain on disk locally under `_obsolete/`, but `.gitignore` prevents them from being pushed again.

## Documentation Updates

- `README.md`: documents `_obsolete/` as local-only ignored archive and notes restored folders.
- `HANDOFF.md`: adds repository cleanup rule: `_obsolete/` is ignored and not pushed; three user-specified folders must not be migrated.
- `docs/ARCHITECTURE.md`: clarifies `_obsolete/` is outside active runtime and GitHub surface.
- `docs/PROJECT_STATE.md`: records current repository cleanup state.
- `docs/CHANGELOG.md`: adds revised 第43轮 cleanup entry.
- `docs/DEV_LOG.md`: records implementation and restoration details.
- `docs/repository-audit.md`: created revised evidence-based inventory.
- `docs/repository-cleanup-report.md`: this final cleanup report.

## GitIgnore Changes

`.gitignore` was rewritten/expanded to cover:

- `_obsolete/` local archive directory
- Build outputs: `build/`, `dist/`, `out/`, `target/`
- Python: `__pycache__/`, `**/__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `coverage/`, `htmlcov/`, `*.py[cod]`
- Node/frontend: `node_modules/`, `.next/`, `.nuxt/`, `.output/`, `.vite/`, `.turbo/`, `.parcel-cache/`
- Runtime/local data: `runtime/`, `projects/*/runtime/`, `*.db`, `*.sqlite`, `*.sqlite3`
- Logs: `logs/`, `*.log`, `/tmp/forge_*.log`, `/tmp/mtplx_*.log`, `/tmp/llama_*.log`
- Temp/cache: `tmp/`, `temp/`, `.cache/`, `*.bak`, `*.swp`, `*.tmp`
- IDE/OS: `.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`

## Compatibility Fix Included

Source/documentation mismatch found: active tests and `debt continue` imported `peer_review.orchestrator`, while the old implementation had previously been archived.  
Action: added `_factory/patterns/peer-review/src/peer_review/orchestrator.py` as a thin lazy compatibility shim that delegates `run_langgraph_review` to the current LangGraph execution path and provides a documented retired `continue_langgraph_review` placeholder.

## Verification

- `python3 -m py_compile _factory/patterns/peer-review/src/peer_review/orchestrator.py` ✅
- `PYTHONPATH=_factory/patterns/peer-review/src python3 -c 'from peer_review.orchestrator import ...'` ✅ for import + retired `continue_langgraph_review` ValueError behavior.
- `make test` in the sandbox is blocked by missing optional/runtime dependencies (`agno`, `llama_index.core`, `chromadb`, `ollama`, `langgraph`, `litellm`, etc.). This was already true before cleanup changes.
- `projects/legal-bot/`, `projects/project-b/`, and `retro-data-share/` are present in the active tree.
- `_obsolete/` is ignored and has zero tracked files in the revised index.

## Remaining Risks

| Risk | Impact | Mitigation / Follow-up |
|---|---|---|
| Sandbox lacks full Mac/LLM runtime dependencies. | Full `make test` cannot be completed here. | Run `make install-dev && make test` on target Mac environment. |
| `projects/legal-bot/` / `projects/project-b/` may be stale. | They increase GitHub surface area. | Retained per explicit user instruction; revisit only with user approval. |
| `retro-data-share/` is generated validation output. | It is not minimal, but user requested restoration. | Retained per explicit user instruction. |
| `continue_langgraph_review` is explicitly retired. | `debt continue` will fail with a clear ValueError until a modern checkpoint resume path exists. | Implement modern LangGraph checkpoint resume if HITL resume becomes required again. |

## Final Repository Structure

```text
.
  .gitignore
  DOCUMENT_AUDIT_REPORT.md
  DOCUMENT_CHANGE_REPORT.md
  HANDOFF.md
  Makefile
  README.md
  backup.sh
  release.sh
  _agents/
    arch-advisor.md
    code-explorer.md
    retro-analyst.md
    security-reviewer.md
  _factory/
    evals/
      gold_dataset.json
    experts/
      _TEMPLATE.expert/
        README.md
        expert.yaml
      compliance-auditor.expert/
        expert.yaml
      debt-lawyer.expert/
        demo_r1_legal_logic.py
        expert.yaml
      execution-strategist.expert/
        expert.yaml
      risk-assessor.expert/
        expert.yaml
    knowledge_pipeline/
      pipeline.py
      provenance_manager.py
      provenance_registry.json
      schemas.py
    lessons/
      2026-Q2-debt-collection.lesson.md
      _TEMPLATE.lesson.md
      test-final-001.lesson.md
    patterns/
      data-acquisition/
        README.md
        pyproject.toml
      expert-consultant/
      fastapi-backend/
        README.md
        pyproject.toml
      ingestion-pipeline/
        README.md
        pyproject.toml
        verify-real.sh
      llm-telemetry/
        README.md
        pyproject.toml
      peer-review/
        pyproject.toml
    skills/
      _TEMPLATE.skill.md
      arch-design.skill.md
      asset-search.skill.md
      compliance-layered.skill.md
      data-acquisition.skill.md
      data-ingestion.skill.md
      data-quality.skill.md
      discovery-interview.skill.md
      prescription-risk.skill.md
      security-review.skill.md
      tdd-cycle.skill.md
  _infra/
    CLAUDE.global.md
    forge-cli.sh
    litellm_gatekeeper.py
    model-routing-rules.md
    setup.sh
    smart_proxy.py
    smart_proxy_streaming.py
    start-litellm.sh
    forge_tools/
      pyproject.toml
      src/
      tests/
        test_cli.py
        test_phases.py
        test_task_graph.py
  config/
    models.yaml
    privacy_policy.yaml
    routing_plans.yaml
  docs/
    ARCHITECTURE.md
    CHANGELOG.md
    DECISIONS.md
    DEPLOYMENT_GUIDE.md
    DEV_LOG.md
    FACTORY_ASSESSMENT.md
    FACTORY_OPERATIONS.md
    GOVERNANCE_CHECK_2026-06-16.md
    GOVERNANCE_CHECK_2026-06-17.md
    GOVERNANCE_CHECK_LATEST.md
    LESSONS_LEARNED_SMART_PROXY_MTPX.md
    PROJECT_STATE.md
    ... (12 more files)
    adr/
      ADR-001-langgraph-migration.md
      ADR-002-dual-file-model-management.md
      ADR-003-data-privacy-gate-and-policy-file.md
      ADR-004-mtplx-as-primary-local-backend.md
      ADR-005-knowledgehub-pure-llamaindex-chromadb.md
      ADR-006-forge-eval-as-ab-testing-capability.md
      ADR-007-memorystore-as-plan-comparison-ssot.md
      README.md
    research/
      anti-ban-crawling-strategy.md
      browser-automation-tools-selection.md
      data-acquisition-feasibility.md
      expert-system-design.md
      ingestion-tools-comparison.md
  retro-data-share/
    01_pytest.txt
    02_security_scan.txt
    03_strategy_glm.txt
    04_strategy_local.txt
  projects/
    _TEMPLATE/
      AGENTS.md
      CHARTER.md
      .claude/
        CLAUDE.md
        lint-runner.sh
        test-runner.sh
      config/
        models.yaml
        privacy_policy.yaml
        routing_plans.yaml
      docs/
        BUILD_LOG.md
        DISCOVERY.md
        RISK.md
        SPEC.md
        TASK_GRAPH.md
    debt-collection/
      .gitignore
      AGENTS.md
      pyproject.toml
      sources.yaml
      .claude/
        CLAUDE.md
        lint-runner.sh
        test-runner.sh
      docs/
        BUILD_LOG.md
        DISCOVERY.md
        RETRO.md
        RISK.md
        SPEC.md
        TASK_GRAPH.md
        collect-retro-data.sh
        strategy-sample-claude.md
      src/
      tests/
        test_debt.py
        test_debt_review.py
    legal-bot/
      AGENTS.md
      CHARTER.md
      .claude/
        CLAUDE.md
        lint-runner.sh
        test-runner.sh
      config/
        models.yaml
        privacy_policy.yaml
        routing_plans.yaml
      docs/
        BUILD_LOG.md
        DISCOVERY.md
        RISK.md
        SPEC.md
        TASK_GRAPH.md
      experts/
      src/
    mini-gratitude/
      AGENTS.md
      CHARTER.md
      .claude/
        CLAUDE.md
        lint-runner.sh
        test-runner.sh
      config/
        models.yaml
        privacy_policy.yaml
        routing_plans.yaml
      docs/
        BUILD_LOG.md
        DISCOVERY.md
        RISK.md
        SPEC.md
        TASK_GRAPH.md
      src/
    project-b/
      AGENTS.md
      CHARTER.md
      .claude/
        CLAUDE.md
        lint-runner.sh
        test-runner.sh
      config/
        models.yaml
        privacy_policy.yaml
        routing_plans.yaml
      docs/
        BUILD_LOG.md
        DISCOVERY.md
        RISK.md
        SPEC.md
        TASK_GRAPH.md
      src/
  scripts/
    benchmark_test.py
    diagnose_proxy.sh
    forge-start.sh
    governance_check.py
    purge_vram.sh
    start_streaming_proxy.sh
    test_streaming_plan.py
```
