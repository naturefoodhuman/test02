<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-06-20 22:20:00 CST
-->

# Repository Audit — FORGE Factory

**Audit date**: 2026-06-20 (Asia/Shanghai)  
**Repository**: `naturefoodhuman/test02`  
**Method**: git tracked-file inventory + source/reference grep + documentation cross-check + baseline command execution.  
**Rule**: Source code is treated as the current truth when it conflicts with older documentation.

## Summary Inventory

- Tracked files after revised cleanup staging: **326**
- Tracked `_obsolete/` files: **0**
- `_obsolete/` policy: **ignored local archive; not pushed to GitHub**
- User-mandated retained folders: `projects/legal-bot/`, `projects/project-b/`, `retro-data-share/`
- Ignored local paths currently detected: **3**

### Active files by top-level area

| Area | Count | Assessment |
|---|---:|---|
| `projects` | 143 | Project templates, active pilot, demos/placeholders explicitly retained by user. |
| `_factory` | 102 | Core factory skills, experts, patterns, peer-review implementation. |
| `docs` | 37 | Current governance, architecture, ADR, state, and runbook documentation. |
| `_infra` | 18 | Infrastructure gateway, smart proxy, forge CLI, setup assets. |
| `scripts` | 12 | Current operational/benchmark/governance scripts after one-off diagnostics were archived locally. |
| `.` | 9 | Root governance or operational file. |
| `_agents` | 4 | Current global agent definitions. |
| `retro-data-share` | 4 | User-mandated retained historical validation output folder. |
| `config` | 3 | Current root model/routing/privacy configuration SSOT. |

### Active files by extension

| Extension | Count |
|---|---:|
| `.md` | 163 |
| `.py` | 93 |
| `.sh` | 33 |
| `.yaml` | 25 |
| `.toml` | 7 |
| `.txt` | 4 |
| `[no ext]` | 3 |
| `.json` | 2 |
| `.example` | 1 |
| `.log` | 1 |

## Active Assets

### Source code
- `_factory/patterns/peer-review/src/peer_review/graph/*`, `platform/*`, `config/*`, `llm_client.py`: current LangGraph + platform-layer peer-review engine.
- `_infra/smart_proxy.py`, `_infra/smart_proxy_streaming.py`, `_infra/forge_tools/src/forge/*`: current infrastructure and CLI code.
- `projects/debt-collection/src/debt/*`: active pilot application used by Makefile, release flow, docs, and tests.
- `_factory/patterns/*`: reusable factory patterns.
- `projects/legal-bot/` and `projects/project-b/`: retained because the user explicitly required these folders not be migrated.

### Configuration
- `config/models.yaml`, `config/routing_plans.yaml`, `config/privacy_policy.yaml`: current root SSOT for model, routing, and privacy policy.
- `_infra/.env.example`, `_infra/model-routing-rules.md`, `_infra/start-litellm.sh`: current gateway startup/config reference.

### Tests / validation
- `_infra/forge_tools/tests/*`, `_factory/patterns/*/tests/*`, and `projects/debt-collection/tests/*` remain active.
- `retro-data-share/` remains tracked because the user explicitly required it to be restored.

## Candidate Obsolete Assets and Final Action

| Asset | Evidence | Final action |
|---|---|---|
| Existing tracked `_obsolete/` | Historical/obsolete assets should not be part of GitHub minimal repository per latest user instruction. | Stopped tracking; `_obsolete/` added to `.gitignore`; local files retained. |
| `forge_diagnose_20260620_152026.log` | Runtime diagnostic log; generated artifact. | Archived locally to `_obsolete/forge_diagnose_20260620_152026.log`; not pushed. |
| `scripts/demo_knowledge_pipeline.py` | Standalone demo/PoC; no active SOP references. | Archived locally under `_obsolete/scripts/`; not pushed. |
| `scripts/e2e_review_test.py` | Historical validation script using retired `peer_review.orchestrator` path; canonical tests remain elsewhere. | Archived locally under `_obsolete/scripts/`; not pushed. |
| `scripts/fix-claude-code.sh` | One-off local repair script with absolute Mac path and home-directory side effects. | Archived locally under `_obsolete/scripts/`; not pushed. |
| `scripts/test_model_direct.py` | One-off local direct-model diagnostic with absolute Mac path/local ports. | Archived locally under `_obsolete/scripts/`; not pushed. |
| `scripts/verify_on_demand_fix.py` | One-off on-demand loading diagnostic with local ports/process killing. | Archived locally under `_obsolete/scripts/`; not pushed. |
| `projects/legal-bot/` | Prior audit considered it old/demo-like. | **Retained/restored by explicit user instruction.** |
| `projects/project-b/` | Prior audit considered it placeholder/old project. | **Retained/restored by explicit user instruction.** |
| `retro-data-share/` | Generated validation output. | **Retained/restored by explicit user instruction.** |

## Unknown Assets / Remaining Review Items

| Asset | Why unknown / risk | Current action |
|---|---|---|
| `projects/mini-gratitude/` | Demo-like, but current Chinese example documentation directly references it. | Retained. |
| `projects/legal-bot/`, `projects/project-b/` | May be stale, but user explicitly required no migration. | Retained. |
| `retro-data-share/` | Generated validation output, but user explicitly required no migration. | Retained. |
| `backup.sh` | Referenced by docs and benchmark; Makefile has overlapping backup target. | Retained; possible future consolidation. |
| `docs/research/*` | Some research docs may drift over time. | Retained; evaluate in dedicated documentation archival pass. |

## Source vs Documentation Differences Found

1. `peer_review.orchestrator` was referenced by tests and `debt continue`, but the active source tree no longer contained that module after a prior cleanup. A thin lazy compatibility shim has been restored at `_factory/patterns/peer-review/src/peer_review/orchestrator.py`; the retired implementation is local-only under ignored `_obsolete/`.
2. Existing `_obsolete/` assets were tracked in GitHub before this round. This conflicts with the user's latest instruction, so they are removed from the index and ignored.
3. Earlier draft cleanup migrated `projects/legal-bot/`, `projects/project-b/`, and `retro-data-share/`; this has been reversed before push.

## Local-only Archive Detail

| Original Path | Local Archive Path | Reason |
|---|---|---|
| `forge_diagnose_20260620_152026.log` | `_obsolete/forge_diagnose_20260620_152026.log` | Runtime diagnostic log; local-only archive because `_obsolete/` is ignored. |
| `scripts/demo_knowledge_pipeline.py` | `_obsolete/scripts/demo_knowledge_pipeline.py` | Standalone demo/PoC script with no active SOP references. |
| `scripts/e2e_review_test.py` | `_obsolete/scripts/e2e_review_test.py` | Historical validation script using retired orchestrator import path; canonical tests remain under peer-review tests. |
| `scripts/fix-claude-code.sh` | `_obsolete/scripts/fix-claude-code.sh` | One-off local machine repair script mutating home-directory config and using absolute Mac path. |
| `scripts/test_model_direct.py` | `_obsolete/scripts/test_model_direct.py` | One-off local-port/direct-model diagnostic with absolute Mac path. |
| `scripts/verify_on_demand_fix.py` | `_obsolete/scripts/verify_on_demand_fix.py` | One-off on-demand-load diagnostic with local ports/process killing. |

## Existing `_obsolete/` Handling

Tracked files previously under `_obsolete/` are removed from Git tracking. Local copies remain under `_obsolete/`, which is ignored and will not be pushed.
