<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-06-20 22:50:00 CST
-->

# Repository Cleanup Report

## Summary

| Metric | Count | Notes |
|---|---:|---|
| Scanned tracked files | 348 | Based on revised git index after restoring `_obsolete/` tracking. |
| Active retained tracked files | 326 | Tracked files outside `_obsolete/`. |
| Tracked `_obsolete/` files | 22 | Required by user: `_obsolete/` is pushed to GitHub. |
| User-requested folders restored/retained active | 3 | `projects/legal-bot/`, `projects/project-b/`, `retro-data-share/`. |

## User-requested Restoration / Retention

These folders remain tracked and active, not migrated:

- `projects/legal-bot/`
- `projects/project-b/`
- `retro-data-share/`

## Obsolete Assets Tracked in GitHub

| Path | Reason |
|---|---|
| `_obsolete/4-Final Architecture Design.md` | Historical design/document artifact; superseded by current docs/ARCHITECTURE.md and ADRs. |
| `_obsolete/5-Architecture Upgrade Execution Plan.md` | Historical design/document artifact; superseded by current docs/ARCHITECTURE.md and ADRs. |
| `_obsolete/README.md` | Obsolete asset migration record. |
| `_obsolete/_factory/patterns/peer-review/src/peer_review/agent_factory.py` | Retired Agno-era peer-review implementation; replaced by LangGraph/platform path. |
| `_obsolete/_factory/patterns/peer-review/src/peer_review/knowledge_loader.py` | Retired Agno-era peer-review implementation; replaced by LangGraph/platform path. |
| `_obsolete/_factory/patterns/peer-review/src/peer_review/orchestrator.py` | Retired Agno-era peer-review implementation; replaced by LangGraph/platform path. |
| `_obsolete/_infra/diag-glm.sh` | Retired/diagnostic infrastructure asset; replaced by current config/startup flow. |
| `_obsolete/_infra/litellm-config.yaml` | Retired/diagnostic infrastructure asset; replaced by current config/startup flow. |
| `_obsolete/_infra/verify-glm.sh` | Retired/diagnostic infrastructure asset; replaced by current config/startup flow. |
| `_obsolete/diag-glm-output.txt` | Historical diagnostic output retained for traceability. |
| `_obsolete/diag-glm-v2-output.txt` | Historical diagnostic output retained for traceability. |
| `_obsolete/docs/AI 项目孵化工厂架构设计书-V4.docx` | Historical design/document artifact; superseded by current docs/ARCHITECTURE.md and ADRs. |
| `_obsolete/docs/AI 项目孵化工厂需求说明书-V2.docx` | Historical design/document artifact; superseded by current docs/ARCHITECTURE.md and ADRs. |
| `_obsolete/forge_diagnose_20260620_152026.log` | Runtime diagnostic log retained for traceability. |
| `_obsolete/scripts/demo_knowledge_pipeline.py` | One-off demo/diagnostic/repair script; not part of current operational SOP. |
| `_obsolete/scripts/e2e_review_test.py` | One-off demo/diagnostic/repair script; not part of current operational SOP. |
| `_obsolete/scripts/fix-claude-code.sh` | One-off demo/diagnostic/repair script; not part of current operational SOP. |
| `_obsolete/scripts/test_model_direct.py` | One-off demo/diagnostic/repair script; not part of current operational SOP. |
| `_obsolete/scripts/verify_on_demand_fix.py` | One-off demo/diagnostic/repair script; not part of current operational SOP. |
| `_obsolete/test_comparison.py` | Historical root-level test/PoC replaced by current test suites. |
| `_obsolete/test_full.py` | Historical root-level test/PoC replaced by current test suites. |
| `_obsolete/test_smoke.py` | Historical root-level test/PoC replaced by current test suites. |

## Documentation Updates

- `README.md`: documents `_obsolete/` as tracked GitHub history archive and notes retained active folders.
- `HANDOFF.md`: adds repository cleanup rule: `_obsolete/` is not ignored and is pushed; three user-specified folders must not be migrated.
- `docs/ARCHITECTURE.md`: clarifies `_obsolete/` is outside active runtime but inside GitHub traceability surface.
- `docs/PROJECT_STATE.md`: records current repository cleanup state.
- `docs/CHANGELOG.md`: adds revised 第43轮 cleanup entry.
- `docs/DEV_LOG.md`: records implementation and restoration details.
- `_obsolete/README.md`: records current obsolete inventory and usage rules.
- `docs/repository-audit.md`: created revised evidence-based inventory.
- `docs/repository-cleanup-report.md`: this final cleanup report.

## GitIgnore Changes

`.gitignore` was expanded to cover build outputs, Python/Node caches, runtime data, logs, temp/cache folders, IDE files, and OS artifacts.

Important final policy: `_obsolete/` is **not** ignored, so GitHub contains obsolete assets for traceability.

## Compatibility Fix Included

Source/documentation mismatch found: active tests and `debt continue` imported `peer_review.orchestrator`, while the old implementation had previously been archived.  
Action: added `_factory/patterns/peer-review/src/peer_review/orchestrator.py` as a thin lazy compatibility shim that delegates `run_langgraph_review` to the current LangGraph execution path and provides a documented retired `continue_langgraph_review` placeholder.

## Verification

- `python3 -m py_compile _factory/patterns/peer-review/src/peer_review/orchestrator.py` ✅
- `PYTHONPATH=_factory/patterns/peer-review/src python3 -c 'from peer_review.orchestrator import ...'` ✅ for import + retired `continue_langgraph_review` ValueError behavior.
- `make test` in the sandbox is blocked by missing optional/runtime dependencies (`agno`, `llama_index.core`, `chromadb`, `ollama`, `langgraph`, `litellm`, etc.). This was already true before cleanup changes.
- `projects/legal-bot/`, `projects/project-b/`, and `retro-data-share/` are present in the active tree.
- `_obsolete/` is tracked and will be pushed to GitHub.

## Remaining Risks

| Risk | Impact | Mitigation / Follow-up |
|---|---|---|
| Sandbox lacks full Mac/LLM runtime dependencies. | Full `make test` cannot be completed here. | Run `make install-dev && make test` on target Mac environment. |
| `projects/legal-bot/` / `projects/project-b/` may be stale. | They increase active GitHub surface area. | Retained per explicit user instruction; revisit only with user approval. |
| `retro-data-share/` is generated validation output. | It is not minimal, but user requested restoration. | Retained per explicit user instruction. |
| `_obsolete/` increases repository size. | GitHub contains historical assets. | Required by latest user instruction for traceability. |
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
  _obsolete/
    4-Final Architecture Design.md
    5-Architecture Upgrade Execution Plan.md
    README.md
    diag-glm-output.txt
    diag-glm-v2-output.txt
    forge_diagnose_20260620_152026.log
    test_comparison.py
    test_full.py
    test_smoke.py
    docs/
      AI 项目孵化工厂架构设计书-V4.docx
      AI 项目孵化工厂需求说明书-V2.docx
    _factory/
      patterns/
    _infra/
      diag-glm.sh
      litellm-config.yaml
      verify-glm.sh
    scripts/
      demo_knowledge_pipeline.py
      e2e_review_test.py
      fix-claude-code.sh
      test_model_direct.py
      verify_on_demand_fix.py
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
