<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-06-20 22:50:00 CST
-->

# Obsolete Assets

`_obsolete/` contains historical, deprecated, generated, or one-off assets that are no longer part of the active runtime / build / deployment surface.

This directory is intentionally tracked and pushed to GitHub for traceability.

## Usage Rules

1. Do **not** delete obsolete assets directly.
2. Preserve original path structure under `_obsolete/<original-path>` whenever it can be confirmed.
3. Record every migration with original path/new path/reason in cleanup reports.
4. Do not import or execute code from `_obsolete/` in current production paths.
5. If an obsolete asset must be revived, copy it back through a reviewed change and update docs/tests.
6. User-mandated active folders `projects/legal-bot/`, `projects/project-b/`, and `retro-data-share/` must not be moved here without explicit approval.

## Current Obsolete Inventory

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
