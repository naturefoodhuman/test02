<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-06-20 22:50:00 CST
-->

# Repository Audit — FORGE Factory

**Audit date**: 2026-06-20 (Asia/Shanghai)  
**Repository**: `naturefoodhuman/test02`  
**Method**: git tracked-file inventory + source/reference grep + documentation cross-check + baseline command execution.  
**Rule**: Source code is treated as the current truth when it conflicts with older documentation.

## Summary Inventory

- Tracked files after revised cleanup staging: **348**
- Active tracked files outside `_obsolete/`: **326**
- Tracked `_obsolete/` files: **22**
- `_obsolete/` policy: **tracked and pushed to GitHub for traceability**
- User-mandated retained active folders: `projects/legal-bot/`, `projects/project-b/`, `retro-data-share/`

### Active files by top-level area

| Area | Count | Assessment |
|---|---:|---|
| `projects` | 143 | Project templates, active pilot, demos/placeholders explicitly retained by user. |
| `_factory` | 102 | Core factory skills, experts, patterns, peer-review implementation. |
| `docs` | 37 | Current governance, architecture, ADR, state, and runbook documentation. |
| `_obsolete` | 22 | Tracked historical/obsolete assets for traceability. |
| `_infra` | 18 | Infrastructure gateway, smart proxy, forge CLI, setup assets. |
| `.` | 8 | Root governance or operational file. |
| `scripts` | 7 | Current operational/benchmark/governance scripts after one-off diagnostics were moved. |
| `_agents` | 4 | Current global agent definitions. |
| `retro-data-share` | 4 | User-mandated retained historical validation output folder. |
| `config` | 3 | Current root model/routing/privacy configuration SSOT. |

### Files by extension

| Extension | Count |
|---|---:|
| `.md` | 166 |
| `.py` | 99 |
| `.sh` | 35 |
| `.yaml` | 26 |
| `.toml` | 7 |
| `.txt` | 6 |
| `[no ext]` | 3 |
| `.json` | 2 |
| `.docx` | 2 |
| `.example` | 1 |
| `.log` | 1 |

## Active Assets

### Source code
- `_factory/patterns/peer-review/src/peer_review/graph/*`, `platform/*`, `config/*`, `llm_client.py`: current LangGraph + platform-layer peer-review engine.
- `_infra/smart_proxy.py`, `_infra/smart_proxy_streaming.py`, `_infra/forge_tools/src/forge/*`: current infrastructure and CLI code.
- `projects/debt-collection/src/debt/*`: active pilot application used by Makefile, release flow, docs, and tests.
- `_factory/patterns/*`: reusable factory patterns.
- `projects/legal-bot/` and `projects/project-b/`: retained active because the user explicitly required these folders not be migrated.

### Configuration
- `config/models.yaml`, `config/routing_plans.yaml`, `config/privacy_policy.yaml`: current root SSOT for model, routing, and privacy policy.
- `_infra/.env.example`, `_infra/model-routing-rules.md`, `_infra/start-litellm.sh`: current gateway startup/config reference.

### Tests / validation
- `_infra/forge_tools/tests/*`, `_factory/patterns/*/tests/*`, and `projects/debt-collection/tests/*` remain active.
- `retro-data-share/` remains tracked active because the user explicitly required it to be restored.

## Obsolete Assets Moved / Tracked

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

## Explicitly Retained Active Assets

| Asset | Reason |
|---|---|
| `projects/legal-bot/` | User explicitly instructed not to migrate; restored/kept active. |
| `projects/project-b/` | User explicitly instructed not to migrate; restored/kept active. |
| `retro-data-share/` | User explicitly instructed not to migrate; restored/kept active. |

## Unknown Assets / Remaining Review Items

| Asset | Why unknown / risk | Current action |
|---|---|---|
| `projects/mini-gratitude/` | Demo-like, but current Chinese example documentation directly references it. | Retained. |
| `projects/legal-bot/`, `projects/project-b/` | May be stale, but user explicitly required no migration. | Retained active. |
| `retro-data-share/` | Generated validation output, but user explicitly required no migration. | Retained active. |
| `backup.sh` | Referenced by docs and benchmark; Makefile has overlapping backup target. | Retained; possible future consolidation. |
| `docs/research/*` | Some research docs may drift over time. | Retained; evaluate in dedicated documentation archival pass. |

## Source vs Documentation Differences Found

1. `peer_review.orchestrator` was referenced by tests and `debt continue`, but the active source tree no longer contained that module after a prior cleanup. A thin lazy compatibility shim has been restored at `_factory/patterns/peer-review/src/peer_review/orchestrator.py`; the retired implementation is tracked under `_obsolete/_factory/patterns/peer-review/src/peer_review/orchestrator.py`.
2. Earlier draft cleanup migrated `projects/legal-bot/`, `projects/project-b/`, and `retro-data-share/`; this was reversed before final push per user instruction.
3. `_obsolete/` policy changed twice during the task; final user instruction is authoritative: `_obsolete/` is **not ignored** and is pushed to GitHub.
