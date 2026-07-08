# PROJECT_DOSSIER_V5.md

**版本**：v1.5.0-current-assets-feos-mvp-validated
**生成日期**：2026-07-07
**生成依据**：当前仓库源码、配置、维护文档、FEOS MVP 实现、用户确认的《全功能最小示例项目》测试结果、治理检查基线
**用途**：当前项目资产卷宗；用于让后续 AI 仅基于本卷宗与经批准的架构设计方案生成工程设计文档或执行开发任务
**保留关系**：`PROJECT_DOSSIER_V4.md` 作为历史资产卷宗保留；本文件为 V5 最新资产卷宗
**状态 SSOT**：当前状态以 `docs/PROJECT_STATE.md` 为准；基础工厂任务状态以 `TASK_BACKLOG.md` §10 为准；FEOS 任务状态以 `FEOS_TASK_BACKLOG.md` 为准

---

## 0. Executive Summary

FORGE Factory 是一个本地优先、可审计、可复用的 AI 项目孵化工厂。它将模糊需求通过五阶段流程、Agent/Skill 协作、本地/外部模型路由、联网搜索与提取、隐私网关、本地 RAG、浏览器/MCP 安全治理、文档治理自动化，以及 FEOS 人工外部升级闭环，转化为可运行、可测试、可交接的软件项目。

截至 V5，本仓库已经具备以下主干能力：

- Core FORGE 五阶段项目孵化能力：DISCOVERY → SPEC → BUILD → HARDEN → RETRO；
- LangGraph HUB-SPOKE 多专家评审能力；
- 双文件模型与路由计划管理：`config/models.yaml` + `config/routing_plans.yaml`；
- Smart Proxy / LiteLLM / MTPLX / Ollama / llama.cpp 本地模型运行链路；
- Claude Code for VS Code 本地模型接入与诊断脚本；
- `_infra/network/` 联网增量模块：Search / Extract / Privacy / RAG / Browser / MCP Guard / Ops / Diagnostics；
- 本地模型运行参数 SSOT：`config/model_runtime.yaml`；
- 文档治理自动化 P2：`make docs-check`、`make governance-check`、自动文档索引和 Agent handoff 摘要；
- MTP / runtime benchmark 与默认运行参数建议；
- `_infra/feos/` FEOS MVP 基础闭环：Case、Evidence、Graph、Context、Package、Clipboard Gateway、Response Ingestion、Verification、Execution Planning、Outcome、Knowledge Distillation、Observability、Diagnostics；
- 《全功能最小示例项目》已按用户确认完成测试并全部通过，当前示例为 `mini-feos-debug-lab`。

本卷宗只记录当前工厂资产、边界、运行方式、配置、验证证据、已知限制和文档组织建议；不定义新的业务系统，不替代任何单独项目的架构设计。

---

## 1. Product Identity

### 1.1 Project Name

FORGE Factory（AI 项目孵化工厂）

### 1.2 One-line Description

在本地 Mac 工作站上，通过五阶段流程、可配置模型路由、多专家评审、隐私治理、联网取数、文档治理和 FEOS 人工升级闭环，把想法孵化为可运行 AI 软件项目。

### 1.3 Primary Users

| 用户 | 需求 |
|---|---|
| 独立开发者 | 用 AI 协助完整开发项目，同时保留本地数据控制权。 |
| 架构师 / 技术合伙人 | 维护一个可复用、可审计、可交接的项目工厂。 |
| AI Agent / Claude Code | 根据文档、规则、任务图安全执行开发任务。 |
| 项目接手者 | 在 5～15 分钟内理解状态、边界、下一步。 |
| 新项目负责人 | 在不污染工厂根文档的前提下启动新项目。 |

### 1.4 Operating Assumptions

- 目标运行环境是 macOS / Apple Silicon / 本地优先。
- 外部 SaaS 可作为 fallback，但不得成为私域数据默认路径。
- 主控交互方式以 Claude Code for VS Code 自然语言对话为主，终端 CLI 作为验证、启动、诊断和自动化辅助。
- FEOS 当前主通道是 Artifact/Clipboard 导出 → 人工粘贴给外部模型 → 人工粘贴回复回来；不会自动调用外部模型，也不会自动执行外部建议。
- 所有高风险动作必须人工确认。
- 所有重大决策必须通过 ADR 记录。

---

## 2. Repository Map

```text
.
├── README.md                          # 人类快速入口
├── HANDOFF.md                         # Agent 接手入口
├── PROJECT_DOSSIER_V3.md              # 历史卷宗
├── PROJECT_DOSSIER_V4.md              # 历史资产卷宗，保留
├── PROJECT_DOSSIER_V5.md              # 当前最新资产卷宗
├── NETWORK_ARCHITECTURE_FINAL.md      # 联网架构基准
├── NETWORK_ENGINEERING_DESIGN.md      # 联网工程设计基准
├── FEOS_ARCHITECTURE_FINAL.md         # FEOS 架构基准
├── FEOS_ENGINEERING_DESIGN.md         # FEOS 工程设计基准
├── FEOS_TASK_BACKLOG.md               # FEOS 任务状态 SSOT
├── TASK_BACKLOG.md                    # 基础工厂任务定义与状态，§10 为状态 SSOT
├── DOCUMENT_AUDIT_REPORT.md           # 文档治理审计基线
├── DOCUMENT_CHANGE_REPORT.md          # 文档治理变更记录
├── config/                            # 全局配置 SSOT
├── docker/                            # SearXNG / Crawl4AI compose
├── _infra/                            # 基础设施、模型代理、network、feos
├── _factory/                          # skills / patterns / lessons / evals
├── _agents/                           # 全局 Agent 定义
├── projects/                          # 项目模板、试点项目、新项目建议放置区
├── scripts/                           # 启动、诊断、治理、运维脚本
├── docs/                              # 当前状态、日志、ADR、培训、治理
├── diagnostics/                       # 诊断产物
├── runtime/                           # 本地运行数据，gitignored
└── .forge/                            # FEOS 等本地运行数据，gitignored
```

---

## 3. Core Documents and SSOT

| 事实类型 | SSOT / 入口 |
|---|---|
| 当前状态 | `docs/PROJECT_STATE.md` |
| Agent 接手规则 | `HANDOFF.md` |
| 当前资产卷宗 | `PROJECT_DOSSIER_V5.md` |
| 历史资产卷宗 | `PROJECT_DOSSIER_V3.md`, `PROJECT_DOSSIER_V4.md` |
| 基础工厂任务状态 | `TASK_BACKLOG.md` §10 |
| FEOS 任务状态 | `FEOS_TASK_BACKLOG.md` |
| 文档索引 | `docs/DOCUMENT_INDEX.md` |
| 新 Agent 自动摘要 | `docs/AGENT_HANDOFF_SUMMARY.md` |
| 联网架构 | `NETWORK_ARCHITECTURE_FINAL.md` |
| 联网工程设计 | `NETWORK_ENGINEERING_DESIGN.md` |
| FEOS 架构 | `FEOS_ARCHITECTURE_FINAL.md` |
| FEOS 工程设计 | `FEOS_ENGINEERING_DESIGN.md` |
| 架构决策 | `docs/adr/README.md` + ADR files |
| 开发流水 | `docs/DEV_LOG.md` |
| 需求变更 | `docs/CHANGELOG.md` |
| 文档治理 | `docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md` |
| 使用培训 | `docs/工厂使用手册.md` |
| 全功能演示 | `docs/全功能最小示例项目.md` |
| 能力覆盖 | `docs/工厂能力覆盖检查.md` |

### 3.1 文档优先级建议

当多个文档对同一事实存在冲突时，建议按以下顺序处理：

1. 用户当前最新明确指令；
2. `HANDOFF.md`；
3. 相关架构文档（例如 `FEOS_ARCHITECTURE_FINAL.md`、`NETWORK_ARCHITECTURE_FINAL.md`）；
4. 相关工程设计文档；
5. 相关任务 backlog；
6. `PROJECT_DOSSIER_V5.md`；
7. `docs/PROJECT_STATE.md`；
8. 源码与测试；
9. 历史卷宗或历史日志。

---

## 4. Current Architecture Overview

### 4.1 Interaction Layer

```text
Human / Claude Code for VS Code
        ↓
Project documents / prompts / @file context
        ↓
Smart Proxy 4000（Anthropic-compatible）
        ↓
Local / API model routing
        ↓
FORGE workflows, Network tools, FEOS tools
```

### 4.2 Model Runtime Layer

```text
Claude Code / forge / project CLI
        ↓
Smart Proxy 4000
        ↓
LiteLLM core gateway 4001 or direct local backend
        ↓
MTPLX 8080 / MTPLX 8082 / llama.cpp 8084 / Ollama 11434
```

### 4.3 Network Layer

```text
Query
  → InputSanitizer
  → MultiSourceSearchOrchestrator
  → SearXNG tiers / Tavily / Serper fallback
  → ExtractorChain
  → Privacy Gateway
  → Local RAG
  → Output with citations
```

### 4.4 Factory Workflow Layer

```text
DISCOVERY
  → SPEC / ADR / TASK_GRAPH / RISK
  → BUILD / TDD / BUILD_LOG
  → HARDEN / SECURITY_REVIEW
  → RETRO / lessons / patterns
```

### 4.5 FEOS MVP Layer

```text
Failure / uncertainty signal
  → FEOS Case
  → Evidence collection
  → Case graph
  → Similarity / hypotheses / policy
  → Context package
  → Escalation package
  → Clipboard export
  → Human external-model round trip
  → Response import / parse
  → Verification
  → Execution plan / outcome evaluation
  → Knowledge distillation
```

FEOS 当前状态是 Clipboard-first MVP 基础闭环：可用于人工升级复杂问题，但仍需要人工判断、人工粘贴、人工确认与本地测试。

---

## 5. Implemented Capability Inventory

### 5.1 Five-stage Factory Workflow

| Capability | Status | Assets |
|---|---|---|
| DISCOVERY | implemented | `docs/DISCOVERY.md` templates, discovery skill |
| SPEC | implemented | arch skill, ADR templates, TASK_GRAPH |
| BUILD | implemented | TDD skill, coder/reviewer hooks |
| HARDEN | implemented | security-reviewer, security skill |
| RETRO | implemented | retro-analyst, lessons, MemoryStore |
| HITL gates | implemented | `forge gate`, documented Gate rules |

### 5.2 Agent and Skill System

| Asset | Purpose |
|---|---|
| `_agents/arch-advisor.md` | Architecture and ADR production. |
| `_agents/security-reviewer.md` | Threat modeling and security review. |
| `_agents/retro-analyst.md` | Retrospective and lesson extraction. |
| `_agents/code-explorer.md` | Repository exploration and handoff analysis. |
| `_factory/skills/*.skill.md` | Phase-specific reusable procedures. |
| `projects/_TEMPLATE/.claude/agents/*` | Project-level coder/reviewer roles. |

### 5.3 Peer Review / LangGraph

| Asset | Purpose |
|---|---|
| `_factory/patterns/peer-review` | LangGraph multi-expert review pattern. |
| `RoutingPlanEngine` | Loads `models.yaml` and `routing_plans.yaml`. |
| `MemoryStore` | Persistent model run records and comparison. |
| `KnowledgeHub` | Local knowledge retrieval and storage. |
| `DataPrivacyGate` | Data outbound control. |

### 5.4 Network Increment

| Module | Implemented Assets |
|---|---|
| Search | `SearXNGProvider`, `MultiSourceSearchOrchestrator`, `EngineCircuitBreaker`, API providers |
| Extract | `Crawl4AIProvider`, `TrafilaturaProvider`, `CurlCffiProvider`, `ExtractorChain` |
| Privacy | Input sanitizer, regex/Presidio/NER/Qwen detectors, replacer, schema validator, canary |
| MCP Guard | scanner, schema hash, mode policy, approval, argument validator, PreToolUse hook |
| Browser | Playwright client/orchestrator/profile/session/action classifier, Chrome private client |
| Local RAG | SQLite schema, embedder, store, KNN fallback |
| Ops | health check, backup, launchd, diagnostics |
| Security Tests | prompt injection, PII bypass, cookie leak, canary E2E |

### 5.5 FEOS MVP

| Subsystem | Implemented Assets |
|---|---|
| Foundation / config | `_infra/feos/__init__.py`, `_infra/feos/defaults/`, `config/feos.yaml`, `_infra/feos/config_loader.py`, `_infra/feos/bootstrap.py` |
| Models | `_infra/feos/models/` with case, evidence, graph, context, package, gateway, response, verification, execution, knowledge models |
| Storage / repositories | `_infra/feos/storage/`, `_infra/feos/repositories/` |
| Case lifecycle | `_infra/feos/case_manager/`, CLI create/status/list/archive |
| Detector | `_infra/feos/detector/` |
| Evidence | `_infra/feos/evidence/`, collectors, parsers, collector registry |
| Graph | `_infra/feos/graph/` |
| Retrieval / hypothesis | `_infra/feos/retrieval/`, `_infra/feos/hypothesis/` |
| Privacy / policy | `_infra/feos/adapters/privacy_adapter.py`, `_infra/feos/policy/` |
| Context / package | `_infra/feos/context/`, `_infra/feos/package/` |
| Rendering / gateways | `_infra/feos/renderers/`, `_infra/feos/gateways/`, `_infra/feos/adapters/clipboard_adapter.py` |
| Ingestion | `_infra/feos/ingestion/` |
| Verification | `_infra/feos/verification/` |
| Execution | `_infra/feos/execution/` |
| Distillation | `_infra/feos/distillation/`, `_infra/feos/adapters/knowledge_os_adapter.py` |
| Observability / diagnostics | `_infra/feos/observability/`, `scripts/diagnostics/feos_case_audit.py` |
| Workflows | `_infra/feos/workflows/clipboard_escalation_workflow.py`, `response_processing_workflow.py`, `execution_closure_workflow.py` |
| Tests | `_infra/feos/tests/unit/`, `security/`, `golden/`, `integration/`, `fixtures/` |

### 5.6 Documentation Governance

| Capability | Status |
|---|---|
| ADR baseline | ADR-001 through ADR-009 |
| `make docs-check` | implemented |
| `make governance-check` | implemented |
| changed-files R5 check | implemented; human-authored files missing LLM header are warning-only, not blocker |
| Backlog ↔ DEV_LOG check | implemented |
| code change ↔ CHANGELOG check | implemented |
| architecture trigger warning | implemented |
| Document index generation | implemented |
| Agent handoff summary generation | implemented |
| GitHub Actions governance workflow | implemented |
| local pre-commit installer | implemented |
| launchd governance check | implemented |

---

## 6. Configuration Inventory

### 6.1 Global Config

| File | Purpose |
|---|---|
| `config/models.yaml` | Model catalog. |
| `config/routing_plans.yaml` | Active model routing plan. |
| `config/model_runtime.yaml` | Local runtime startup SSOT. |
| `config/network.yaml` | Network module config. |
| `config/privacy_policy.yaml` | Privacy / outbound data policy. |
| `config/mcp_lockfile.yaml` | MCP server pinning. |
| `config/mode_policies.yaml` | MCP mode permissions. |
| `config/domain_reputation.yaml` | Search result scoring. |
| `config/canary_tokens.yaml` | Canary token policy. |
| `config/feos.yaml` | FEOS global config override. |

### 6.2 FEOS Config Priority

FEOS 配置加载顺序：

```text
_infra/feos/defaults/feos.yaml
  → config/feos.yaml
  → .forge/feos/policies/*.yaml / renderer_profiles/*.yaml
  → .env / _infra/.env
  → environment variables
  → CLI flags
```

默认策略：

- `clipboard.enabled=true`；
- `api.enabled=false`；
- `mcp.enabled=false`；
- `browser.enabled=false`；
- `cloud_agent.enabled=false`；
- `.forge/feos/` 下 runtime 数据不进 Git。

### 6.3 Local Secret Files

真实密钥必须只保留在本地且 gitignored：

```text
.env
_infra/.env
```

模板文件：

```text
.env.example
_infra/.env.example
```

---

## 7. Local Model Runtime Inventory

### 7.1 Current Runtime SSOT

```text
config/model_runtime.yaml
```

Helper:

```text
_infra/model_runtime.py
```

### 7.2 Configured Local Models

| Role | Backend | Model | Port |
|---|---|---|---:|
| Primary brain | MTPLX | `Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality` | 8080 |
| Independent reviewer | MTPLX | `Youssofal/Gemma4-MTPLX-Optimized-Quality` | 8082 |
| Deep reviewer | llama.cpp | `Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf` | 8084 |
| Coding test | Ollama | `qwen3-coder-next:q4_K_M` | 11434 |
| Reviewer | Ollama | `deepseek-r1:32b` | 11434 |

### 7.3 Current Runtime Conclusion

- Qwen 8080 default remains MTP depth3.
- KV q8/q4 remain optional, not default.
- no-MTP is a fast-interactive candidate, not the default primary model profile.
- Ollama env includes `OLLAMA_FLASH_ATTENTION=1` and `OLLAMA_KV_CACHE_TYPE=q4_0`.
- MTPLX logs prove sustained MTP runtime and native draft head are active.

---

## 8. Runtime and Diagnostics Commands

### 8.1 Start / Stop

```bash
bash scripts/forge-start.sh
scripts/model_status.sh
scripts/stop_local_models.sh
scripts/stop_local_models.sh --all
```

### 8.2 Network

```bash
python3 -m _infra.network.cli config
python3 -m _infra.network.cli health
python3 -m _infra.network.cli search "python langgraph state machine" --mode research
```

### 8.3 FEOS CLI

```bash
python3 -m _infra.feos.cli create --title "demo" --user-goal "debug with evidence" --json
python3 -m _infra.feos.cli list --json
python3 -m _infra.feos.cli status <case_id> --json
python3 -m _infra.feos.cli export <case_id> --json
python3 -m _infra.feos.cli import response <case_id> --file _infra/feos/tests/fixtures/external_response.md --json
python3 -m _infra.feos.cli response parse <case_id> --json
python3 -m _infra.feos.cli verify <case_id> --json
python3 -m _infra.feos.cli plan <case_id> --json
python3 -m _infra.feos.cli outcome evaluate <case_id> --file _infra/feos/tests/fixtures/outcome.yaml --json
python3 -m _infra.feos.cli distill <case_id> --json
```

### 8.4 Governance

```bash
make docs-check
make governance-check
make network-test
make feos-test
make install-governance-hooks
```

### 8.5 Runtime Diagnostics

```bash
python3 scripts/diagnostics/test_local_streaming.py
python3 scripts/diagnostics/test_mtp_effectiveness.py
python3 scripts/diagnostics/benchmark_local_runtime.py
python3 scripts/diagnostics/feos_case_audit.py <case_id>
```

---

## 9. Current Validation Evidence

### 9.1 FEOS Test Baseline

```text
make feos-test
110 passed
```

### 9.2 Network Test Baseline

```text
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
358 passed, 3 skipped, 44 warnings
```

### 9.3 Governance Baseline

```text
python3 scripts/governance_check.py --strict
Blockers: 0
```

Governance may emit non-blocking architecture-trigger warnings for sensitive terms; blockers are the decisive signal.

### 9.4 Full Demo Baseline

```text
docs/全功能最小示例项目.md
mini-feos-debug-lab
用户确认：已测试完成，全部通过
```

### 9.5 Runtime Benchmark Baseline

Final benchmark artifact:

```text
diagnostics/local_runtime_benchmark/20260626_181952
```

Final runtime recommendation:

```text
Primary default: MTP depth3
Do not default: KV q8/q4
Candidate future profile: no-MTP fast-interactive
```

---

## 10. Current Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Local models slower than official Claude on long context | Longer wait time | Split tasks, use @file, use model_status/stop scripts |
| MTPLX true token-by-token streaming not fully proven | UI may receive pseudo-streaming | Smart Proxy emits Anthropic SSE; diagnostics available |
| Search scraping engines remain IP-risky | CAPTCHA / 429 | Engine Matrix, Circuit Breaker, Tavily/Serper fallback |
| Browser/private workflows require careful operation | Data leakage risk | MCP Guard, mode isolation, high-risk approval |
| FEOS MVP is broad but still skeletal in some advanced checks | Real complex cases may need extra hardening | Start with `mini-feos-debug-lab`, add fixture-driven tests before expanding |
| FEOS API/MCP/Browser/Cloud gateways are disabled stubs | No automated external model channel | Use Clipboard-first manual workflow unless architecture is explicitly approved |
| FEOS response parsing and verification are deterministic/minimal | External responses may require manual review | Treat verification as guardrail, not final truth |
| `.forge/feos/` runtime data is gitignored | Case evidence not shared by default | Export packages deliberately when handoff requires it |
| Historical docs may contain old project names or older status lines | New agents may be confused | Prefer V5 + `docs/PROJECT_STATE.md` + generated document index |

---

## 11. Engineering Design Generation Inputs

An AI generating a future `ENGINEERING_DESIGN.md` from this dossier and an approved architecture design should extract:

1. Repository structure and ownership boundaries from §2.
2. Current SSOT and document priority from §3.
3. Current architecture layers from §4.
4. Capability inventory from §5.
5. Configuration SSOT and FEOS config priority from §6.
6. Runtime and model constraints from §7.
7. Commands and diagnostics from §8.
8. Validation evidence from §9.
9. Known limitations from §10.
10. Governance rules from `docs/adr/ADR-008-documentation-governance-automation.md`.
11. Runtime configuration rules from `docs/adr/ADR-009-local-model-runtime-configuration.md`.
12. If the target is FEOS, use `FEOS_ARCHITECTURE_FINAL.md` + `FEOS_ENGINEERING_DESIGN.md` + `FEOS_TASK_BACKLOG.md` as task/source constraints.

The generated engineering design must not assume new infrastructure. It must preserve current module boundaries unless a new ADR explicitly changes them.

---

## 12. Suggested Future Extension Procedure

Before implementing any major new capability:

1. Read `HANDOFF.md`.
2. Read `PROJECT_DOSSIER_V5.md`.
3. Read `docs/PROJECT_STATE.md`.
4. Read relevant ADRs.
5. Draft architecture/design first.
6. Add or update ADR if architecture or boundaries change.
7. Add tasks to the correct backlog file.
8. Implement incrementally with tests.
9. Run relevant tests plus `make docs-check`.
10. Update DEV_LOG / CHANGELOG / PROJECT_STATE.
11. If a new durable capability is added, refresh the current dossier version.

---

## 13. New Project Document Organization Recommendation

用户接下来可能使用工厂能力新开项目，并可能放入新的 `ARCHITECTURE_FINAL.md`、`ENGINEERING_DESIGN.md`、`TASK_BACKLOG.md` 等文档。为避免旧根文档干扰新项目开发，建议采用“工厂根文档”和“项目文档”隔离策略。

### 13.1 Recommended Layout

推荐把新项目放入独立目录：

```text
projects/<new-project-slug>/
├── README.md
├── docs/
│   ├── ARCHITECTURE_FINAL.md
│   ├── ENGINEERING_DESIGN.md
│   ├── TASK_BACKLOG.md
│   ├── PROJECT_STATE.md
│   ├── DEV_LOG.md
│   ├── CHANGELOG.md
│   ├── ADR/
│   │   └── ADR-001-*.md
│   └── HANDOFF.md
├── src/ or app/
├── tests/
└── runtime/ or .local/                 # gitignored, if needed
```

如果新项目目前只有文档、暂不写代码，也可以先放入：

```text
docs/projects/<new-project-slug>/
├── ARCHITECTURE_FINAL.md
├── ENGINEERING_DESIGN.md
├── TASK_BACKLOG.md
├── PROJECT_STATE.md
└── HANDOFF.md
```

待进入实现阶段，再迁移到 `projects/<new-project-slug>/`。

### 13.2 Avoid Root Name Collision

不建议在根目录直接新增无前缀的：

```text
ARCHITECTURE_FINAL.md
ENGINEERING_DESIGN.md
TASK_BACKLOG.md
PROJECT_STATE.md
HANDOFF.md
```

原因：根目录已有工厂级、Network、FEOS 等长期文档。无前缀新文档容易被 AI 当作工厂级 SSOT，造成上下文污染。

如果必须暂时放在根目录，建议使用项目前缀：

```text
<PROJECT>_ARCHITECTURE_FINAL.md
<PROJECT>_ENGINEERING_DESIGN.md
<PROJECT>_TASK_BACKLOG.md
<PROJECT>_PROJECT_STATE.md
```

但这只是过渡方案；长期仍建议移入 `projects/<new-project-slug>/docs/`。

### 13.3 Root Documents Should Remain Factory-level

根目录应只保留：

- 工厂级入口：`README.md`, `HANDOFF.md`；
- 工厂级状态/卷宗：`PROJECT_DOSSIER_V*.md`；
- 工厂级/模块级已批准架构：`NETWORK_*`, `FEOS_*`；
- 工厂级 backlog：`TASK_BACKLOG.md`；
- 审计/治理文档：`DOCUMENT_AUDIT_REPORT.md`, `DOCUMENT_CHANGE_REPORT.md`。

### 13.4 New Project Handoff Header

每个新项目建议有自己的 `projects/<slug>/docs/HANDOFF.md`，开头明确写：

```text
本目录是 <项目名> 的项目级文档。
不得把根目录 TASK_BACKLOG.md / FEOS_TASK_BACKLOG.md 当作本项目任务状态。
本项目 SSOT：本目录 docs/PROJECT_STATE.md 与 docs/TASK_BACKLOG.md。
工厂能力只作为执行工具和基础设施复用。
```

### 13.5 Suggested AI Prompt for New Project Work

启动新项目时，建议给 AI 的第一段指令包含：

```text
本次任务只处理 projects/<new-project-slug>/ 内的新项目。
根目录文档仅作为工厂能力和治理规则参考，不作为本项目需求来源。
本项目架构以 projects/<new-project-slug>/docs/ARCHITECTURE_FINAL.md 为准。
本项目工程设计以 projects/<new-project-slug>/docs/ENGINEERING_DESIGN.md 为准。
本项目任务状态以 projects/<new-project-slug>/docs/TASK_BACKLOG.md 为准。
如发现根目录旧文档与本项目文档冲突，先报告，不要自动合并。
```

---

## 14. Current Repository Health Summary

```text
Core FORGE: implemented and usable
Network Increment: finalized and tested
Claude Code local model: usable
Local model runtime: centralized and benchmarked
Documentation governance: automated P2
Training docs: FEOS MVP 基础闭环版
Full demo: mini-feos-debug-lab tested by user and passed
FEOS MVP: implemented through FEOS-056 with 110 passing tests
Current state: ready to start a new isolated project using factory capabilities
```

---

## 15. Final Notes

This V5 dossier is intentionally an asset-focused current-state record. It does not define or prescribe a new business system. Future project engineering design should use this file as factual factory input and combine it with a separately approved project architecture design.
