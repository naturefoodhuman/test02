<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-25 20:10:55
-->

# Document Index（自动生成）

本文件由 `scripts/governance_check.py` 自动生成，用于标记当前文档的用途与状态。不要手工编辑；修改分类规则后重新运行 `make governance-check`。

## 状态说明

| 状态 | 含义 |
|---|---|
| current | 当前有效文档，可作为当前事实来源或操作入口。 |
| reference | 参考资料，不应覆盖 SSOT。 |
| runtime-artifact | 运行/诊断产物，通常不应作为设计依据。 |

## 文档清单

| 文档 | 分类 | 状态 |
|---|---|---|
| `DOCUMENT_AUDIT_REPORT.md` | governance | current |
| `DOCUMENT_CHANGE_REPORT.md` | governance | current |
| `HANDOFF.md` | SSOT | current |
| `NETWORK_ARCHITECTURE_FINAL.md` | SSOT | current |
| `NETWORK_ENGINEERING_DESIGN.md` | SSOT | current |
| `PROJECT_DOSSIER_V3.md` | root-doc | reference |
| `README.md` | SSOT | current |
| `TASK_BACKLOG.md` | SSOT | current |
| `_agents/arch-advisor.md` | root-doc | reference |
| `_agents/code-explorer.md` | root-doc | reference |
| `_agents/retro-analyst.md` | root-doc | reference |
| `_agents/security-reviewer.md` | root-doc | reference |
| `_factory/experts/_TEMPLATE.expert/README.md` | root-doc | reference |
| `_factory/experts/_TEMPLATE.expert/knowledge/_gaps.md` | root-doc | reference |
| `_factory/experts/compliance-auditor.expert/knowledge/negation_cases.md` | root-doc | reference |
| `_factory/experts/debt-lawyer.expert/knowledge/ATOM-DAA19406.md` | root-doc | reference |
| `_factory/experts/debt-lawyer.expert/knowledge/_gaps.md` | root-doc | reference |
| `_factory/experts/debt-lawyer.expert/knowledge/practical_qa_highlights.md` | root-doc | reference |
| `_factory/experts/debt-lawyer.expert/knowledge/statutes_summary.md` | root-doc | reference |
| `_factory/experts/debt-lawyer.expert/knowledge/民间借贷纠纷办案手册（1.0版） (法信).md` | root-doc | reference |
| `_factory/experts/execution-strategist.expert/knowledge/local_enforcement.md` | root-doc | reference |
| `_factory/experts/risk-assessor.expert/knowledge/case_patterns.md` | root-doc | reference |
| `_factory/experts/risk-assessor.expert/knowledge/execution_patterns.md` | root-doc | reference |
| `_factory/lessons/2026-Q2-debt-collection.lesson.md` | root-doc | reference |
| `_factory/lessons/_TEMPLATE.lesson.md` | root-doc | reference |
| `_factory/lessons/test-final-001.lesson.md` | root-doc | reference |
| `_factory/patterns/data-acquisition/README.md` | root-doc | reference |
| `_factory/patterns/fastapi-backend/README.md` | root-doc | reference |
| `_factory/patterns/ingestion-pipeline/README.md` | root-doc | reference |
| `_factory/patterns/llm-telemetry/README.md` | root-doc | reference |
| `_factory/skills/_TEMPLATE.skill.md` | root-doc | reference |
| `_factory/skills/arch-design.skill.md` | root-doc | reference |
| `_factory/skills/asset-search.skill.md` | root-doc | reference |
| `_factory/skills/compliance-layered.skill.md` | root-doc | reference |
| `_factory/skills/data-acquisition.skill.md` | root-doc | reference |
| `_factory/skills/data-ingestion.skill.md` | root-doc | reference |
| `_factory/skills/data-quality.skill.md` | root-doc | reference |
| `_factory/skills/discovery-interview.skill.md` | root-doc | reference |
| `_factory/skills/prescription-risk.skill.md` | root-doc | reference |
| `_factory/skills/security-review.skill.md` | root-doc | reference |
| `_factory/skills/tdd-cycle.skill.md` | root-doc | reference |
| `_infra/CLAUDE.global.md` | root-doc | reference |
| `_infra/model-routing-rules.md` | root-doc | reference |
| `_infra/network/README.md` | root-doc | reference |
| `_infra/network/config_loader/README.md` | root-doc | reference |
| `docker/README.md` | root-doc | reference |
| `docs/CHANGELOG.md` | SSOT | current |
| `docs/DECISIONS.md` | supporting-doc | reference |
| `docs/DEPLOYMENT_GUIDE.md` | supporting-doc | reference |
| `docs/DEV_LOG.md` | SSOT | current |
| `docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md` | governance | current |
| `docs/DOCUMENT_INDEX.md` | governance | current |
| `docs/GOVERNANCE_CHECK_2026-06-16.md` | governance | current |
| `docs/GOVERNANCE_CHECK_2026-06-17.md` | governance | current |
| `docs/GOVERNANCE_CHECK_2026-06-25.md` | governance | current |
| `docs/GOVERNANCE_CHECK_LATEST.md` | governance | current |
| `docs/PROJECT_STATE.md` | SSOT | current |
| `docs/RETRO.md` | supporting-doc | reference |
| `docs/SEARCH_ENGINE_RISK_CONTROL_REPORT.md` | supporting-doc | reference |
| `docs/UPGRADE_COMPLETION.md` | supporting-doc | reference |
| `docs/adr/ADR-001-langgraph-migration.md` | governance | current |
| `docs/adr/ADR-002-dual-file-model-management.md` | governance | current |
| `docs/adr/ADR-003-data-privacy-gate-and-policy-file.md` | governance | current |
| `docs/adr/ADR-004-mtplx-as-primary-local-backend.md` | governance | current |
| `docs/adr/ADR-005-knowledgehub-pure-llamaindex-chromadb.md` | governance | current |
| `docs/adr/ADR-006-forge-eval-as-ab-testing-capability.md` | governance | current |
| `docs/adr/ADR-007-memorystore-as-plan-comparison-ssot.md` | governance | current |
| `docs/adr/README.md` | SSOT | current |
| `docs/benchmark.md` | supporting-doc | reference |
| `docs/research/README.md` | research | reference |
| `docs/research/anti-ban-crawling-strategy.md` | research | reference |
| `docs/research/browser-automation-tools-selection.md` | research | reference |
| `docs/research/data-acquisition-feasibility.md` | research | reference |
| `docs/research/expert-system-design.md` | research | reference |
| `docs/research/ingestion-tools-comparison.md` | research | reference |
| `docs/全功能最小示例项目.md` | training | current |
| `docs/工厂使用手册.md` | training | current |
| `docs/工厂能力覆盖检查.md` | training | current |
| `profiles/README.md` | root-doc | reference |
| `profiles/ai-private-github/README.md` | root-doc | reference |
| `profiles/ai-public/README.md` | root-doc | reference |
| `projects/_TEMPLATE/.claude/CLAUDE.md` | root-doc | reference |
| `projects/_TEMPLATE/.claude/agents/coder.md` | root-doc | reference |
| `projects/_TEMPLATE/.claude/agents/reviewer.md` | root-doc | reference |
| `projects/_TEMPLATE/AGENTS.md` | root-doc | reference |
| `projects/_TEMPLATE/CHARTER.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/BUILD_LOG.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/DISCOVERY.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/RISK.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/SPEC.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/TASK_GRAPH.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/adr/ADR-000-template.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/external-review/_INPUT_TEMPLATE.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/harden/SECURITY_REVIEW.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/specs/example-feature/acceptance.md` | root-doc | reference |
| `projects/_TEMPLATE/docs/specs/example-feature/spec.md` | root-doc | reference |
| `projects/debt-collection/.claude/CLAUDE.md` | root-doc | reference |
| `projects/debt-collection/.claude/agents/coder.md` | root-doc | reference |
| `projects/debt-collection/.claude/agents/reviewer.md` | root-doc | reference |
| `projects/debt-collection/AGENTS.md` | root-doc | reference |
| `projects/debt-collection/docs/BUILD_LOG.md` | root-doc | reference |
| `projects/debt-collection/docs/DISCOVERY.md` | root-doc | reference |
| `projects/debt-collection/docs/RETRO.md` | root-doc | reference |
| `projects/debt-collection/docs/RISK.md` | root-doc | reference |
| `projects/debt-collection/docs/SPEC.md` | root-doc | reference |
| `projects/debt-collection/docs/TASK_GRAPH.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-000-template.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-001-local-cli-sqlite.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-002-glm-first-anti-hallucination.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-003-compliant-acquisition-only.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-004-execution-feasibility-first.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-005-local-sensitive-data.md` | root-doc | reference |
| `projects/debt-collection/docs/adr/ADR-006-dynamic-case-intel.md` | root-doc | reference |
| `projects/debt-collection/docs/external-review/_INPUT_TEMPLATE.md` | root-doc | reference |
| `projects/debt-collection/docs/harden/HARDEN_CHECKLIST.md` | root-doc | reference |
| `projects/debt-collection/docs/harden/SECURITY_REVIEW.md` | root-doc | reference |
| `projects/debt-collection/docs/specs/example-feature/acceptance.md` | root-doc | reference |
| `projects/debt-collection/docs/specs/example-feature/spec.md` | root-doc | reference |
| `projects/debt-collection/docs/strategy-sample-claude.md` | root-doc | reference |
| `projects/legal-bot/.claude/CLAUDE.md` | root-doc | reference |
| `projects/legal-bot/.claude/agents/coder.md` | root-doc | reference |
| `projects/legal-bot/.claude/agents/reviewer.md` | root-doc | reference |
| `projects/legal-bot/AGENTS.md` | root-doc | reference |
| `projects/legal-bot/CHARTER.md` | root-doc | reference |
| `projects/legal-bot/docs/BUILD_LOG.md` | root-doc | reference |
| `projects/legal-bot/docs/DISCOVERY.md` | root-doc | reference |
| `projects/legal-bot/docs/RISK.md` | root-doc | reference |
| `projects/legal-bot/docs/SPEC.md` | root-doc | reference |
| `projects/legal-bot/docs/TASK_GRAPH.md` | root-doc | reference |
| `projects/legal-bot/docs/adr/ADR-000-template.md` | root-doc | reference |
| `projects/legal-bot/docs/external-review/_INPUT_TEMPLATE.md` | root-doc | reference |
| `projects/legal-bot/docs/harden/SECURITY_REVIEW.md` | root-doc | reference |
| `projects/legal-bot/docs/specs/example-feature/acceptance.md` | root-doc | reference |
| `projects/legal-bot/docs/specs/example-feature/spec.md` | root-doc | reference |
| `projects/legal-bot/experts/debt-lawyer.expert/knowledge/_gaps.md` | root-doc | reference |
| `projects/legal-bot/experts/debt-lawyer.expert/knowledge/practical_qa_highlights.md` | root-doc | reference |
| `projects/legal-bot/experts/debt-lawyer.expert/knowledge/statutes_summary.md` | root-doc | reference |
| `projects/legal-bot/experts/debt-lawyer.expert/knowledge/民间借贷纠纷办案手册（1.0版） (法信).md` | root-doc | reference |
| `projects/mini-gratitude/.claude/CLAUDE.md` | root-doc | reference |
| `projects/mini-gratitude/.claude/agents/coder.md` | root-doc | reference |
| `projects/mini-gratitude/.claude/agents/reviewer.md` | root-doc | reference |
| `projects/mini-gratitude/AGENTS.md` | root-doc | reference |
| `projects/mini-gratitude/CHARTER.md` | root-doc | reference |
| `projects/mini-gratitude/docs/BUILD_LOG.md` | root-doc | reference |
| `projects/mini-gratitude/docs/DISCOVERY.md` | root-doc | reference |
| `projects/mini-gratitude/docs/RISK.md` | root-doc | reference |
| `projects/mini-gratitude/docs/SPEC.md` | root-doc | reference |
| `projects/mini-gratitude/docs/TASK_GRAPH.md` | root-doc | reference |
| `projects/mini-gratitude/docs/adr/ADR-000-template.md` | root-doc | reference |
| `projects/mini-gratitude/docs/external-review/_INPUT_TEMPLATE.md` | root-doc | reference |
| `projects/mini-gratitude/docs/harden/SECURITY_REVIEW.md` | root-doc | reference |
| `projects/mini-gratitude/docs/specs/example-feature/acceptance.md` | root-doc | reference |
| `projects/mini-gratitude/docs/specs/example-feature/spec.md` | root-doc | reference |
| `projects/project-b/.claude/CLAUDE.md` | root-doc | reference |
| `projects/project-b/.claude/agents/coder.md` | root-doc | reference |
| `projects/project-b/.claude/agents/reviewer.md` | root-doc | reference |
| `projects/project-b/AGENTS.md` | root-doc | reference |
| `projects/project-b/CHARTER.md` | root-doc | reference |
| `projects/project-b/docs/BUILD_LOG.md` | root-doc | reference |
| `projects/project-b/docs/DISCOVERY.md` | root-doc | reference |
| `projects/project-b/docs/RISK.md` | root-doc | reference |
| `projects/project-b/docs/SPEC.md` | root-doc | reference |
| `projects/project-b/docs/TASK_GRAPH.md` | root-doc | reference |
| `projects/project-b/docs/adr/ADR-000-template.md` | root-doc | reference |
| `projects/project-b/docs/external-review/_INPUT_TEMPLATE.md` | root-doc | reference |
| `projects/project-b/docs/harden/SECURITY_REVIEW.md` | root-doc | reference |
| `projects/project-b/docs/specs/example-feature/acceptance.md` | root-doc | reference |
| `projects/project-b/docs/specs/example-feature/spec.md` | root-doc | reference |
| `scripts/diagnostics/README.md` | root-doc | reference |
| `scripts/launchd/README.md` | root-doc | reference |

## 当前 SSOT 快速入口

- 项目接手：`HANDOFF.md`
- 当前状态：`docs/PROJECT_STATE.md`
- 任务状态：`TASK_BACKLOG.md` §10
- 联网架构：`NETWORK_ARCHITECTURE_FINAL.md`
- 联网工程设计：`NETWORK_ENGINEERING_DESIGN.md`
- ADR：`docs/adr/README.md`
- 新用户培训：`docs/工厂使用手册.md`
- 全功能示例：`docs/全功能最小示例项目.md`
- 能力覆盖：`docs/工厂能力覆盖检查.md`
- 治理自动化：`docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`
