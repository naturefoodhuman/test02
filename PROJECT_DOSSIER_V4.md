<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-01 00:00:00
-->

# PROJECT_DOSSIER_V4.md

**版本**：v1.4.10-dossier-current-assets
**生成日期**：2026-07-01
**生成依据**：当前仓库源码、配置、维护文档、治理报告、真机验证记录
**用途**：当前项目资产卷宗；用于让后续 AI 仅基于本卷宗与架构设计方案生成工程设计文档
**状态 SSOT**：当前状态以 `docs/PROJECT_STATE.md` 为准；任务状态以 `TASK_BACKLOG.md` §10 为准。

---

## 0. Executive Summary

FORGE Factory 是一个本地优先、可审计、可复用的 AI 项目孵化工厂。它将模糊需求通过五阶段流程、Agent/Skill 协作、本地/外部模型路由、联网搜索与提取、隐私网关、本地 RAG、浏览器/MCP 安全治理和文档治理自动化，转化为可运行、可测试、可交接的软件项目。

截至本卷宗生成时，项目已经完成：

- Core FORGE 五阶段项目孵化能力；
- LangGraph HUB-SPOKE 多专家评审能力；
- 双文件模型与路由计划管理；
- Smart Proxy / LiteLLM / MTPLX / Ollama / llama.cpp 本地模型运行链路；
- `_infra/network/` 联网增量模块；
- Search / Extract / Privacy / RAG / Browser / MCP Guard / Ops / Diagnostics；
- Claude Code for VS Code 本地模型接入；
- 本地模型运行参数 SSOT：`config/model_runtime.yaml`；
- 文档治理自动化 P2：`make docs-check`、`make governance-check`、自动文档索引和 Agent handoff 摘要；
- MTP / runtime benchmark 与最终默认运行参数建议。

本卷宗不定义下一阶段业务系统，不引入新的目标产品，只完整记录当前资产、边界、运行方式和可扩展点。

---

## 1. Product Identity

### 1.1 Project Name

FORGE Factory（AI 项目孵化工厂）

### 1.2 One-line Description

在本地 Mac 工作站上，通过五阶段流程、可配置模型路由、多专家评审、隐私治理和联网取数能力，把想法孵化为可运行 AI 软件项目。

### 1.3 Primary Users

| 用户 | 需求 |
|---|---|
| 独立开发者 | 用 AI 协助完整开发项目，保留本地数据控制权。 |
| 架构师 / 技术合伙人 | 维护一个可复用、可审计、可交接的项目工厂。 |
| AI Agent / Claude Code | 根据文档、规则、任务图安全执行开发任务。 |
| 项目接手者 | 在 5～15 分钟内理解状态、边界、下一步。 |

### 1.4 Operating Assumptions

- 目标运行环境是 macOS / Apple Silicon / 本地优先。
- 外部 SaaS 可作为 fallback，但不得成为私域数据默认路径。
- 主控交互方式以 Claude Code for VS Code 自然语言对话为主，终端 CLI 作为验证、启动、诊断和自动化辅助。
- 所有高风险动作必须人工确认。
- 所有重大决策必须通过 ADR 记录。

---

## 2. Repository Map

```text
.
├── README.md                          # 人类快速入口
├── HANDOFF.md                         # Agent 接手入口
├── PROJECT_DOSSIER_V3.md              # 历史卷宗
├── PROJECT_DOSSIER_V4.md              # 当前资产卷宗
├── NETWORK_ARCHITECTURE_FINAL.md      # 联网架构基准
├── NETWORK_ENGINEERING_DESIGN.md      # 联网工程设计基准
├── TASK_BACKLOG.md                    # 任务定义与状态，§10 为状态 SSOT
├── DOCUMENT_AUDIT_REPORT.md           # 文档治理审计基线
├── DOCUMENT_CHANGE_REPORT.md          # 文档治理变更记录
├── config/                            # 全局配置 SSOT
├── docker/                            # SearXNG / Crawl4AI compose
├── _infra/                            # 基础设施、模型代理、联网模块
├── _factory/                          # skills / patterns / lessons / evals
├── _agents/                           # 全局 Agent 定义
├── projects/                          # 项目模板和试点项目
├── scripts/                           # 启动、诊断、治理、运维脚本
├── docs/                              # 当前状态、日志、ADR、培训、治理
├── diagnostics/                       # 诊断产物
└── runtime/                           # 本地运行数据，gitignored
```

---

## 3. Core Documents and SSOT

| 事实类型 | SSOT |
|---|---|
| 当前状态 | `docs/PROJECT_STATE.md` |
| 任务状态 | `TASK_BACKLOG.md` §10 |
| Agent 接手规则 | `HANDOFF.md` |
| 文档索引 | `docs/DOCUMENT_INDEX.md` |
| 新 Agent 自动摘要 | `docs/AGENT_HANDOFF_SUMMARY.md` |
| 联网架构 | `NETWORK_ARCHITECTURE_FINAL.md` |
| 联网工程设计 | `NETWORK_ENGINEERING_DESIGN.md` |
| 架构决策 | `docs/adr/README.md` + ADR files |
| 开发流水 | `docs/DEV_LOG.md` |
| 需求变更 | `docs/CHANGELOG.md` |
| 文档治理 | `docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md` |
| 使用培训 | `docs/工厂使用手册.md` |
| 全功能演示 | `docs/全功能最小示例项目.md` |
| 能力覆盖 | `docs/工厂能力覆盖检查.md` |

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
FORGE workflows and tools
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

### 5.5 Documentation Governance

| Capability | Status |
|---|---|
| ADR baseline | ADR-001 through ADR-009 |
| `make docs-check` | implemented |
| `make governance-check` | implemented |
| changed-files R5 check | implemented |
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

### 6.2 Local Secret Files

Real secrets must stay local and gitignored:

```text
.env
_infra/.env
```

Template files:

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

### 8.3 Governance

```bash
make docs-check
make governance-check
make network-test
make install-governance-hooks
```

### 8.4 Runtime Diagnostics

```bash
python3 scripts/diagnostics/test_local_streaming.py
python3 scripts/diagnostics/test_mtp_effectiveness.py
python3 scripts/diagnostics/benchmark_local_runtime.py
```

---

## 9. Current Validation Evidence

### 9.1 Test Baseline

```text
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
358 passed, 3 skipped, 44 warnings
```

### 9.2 Governance Baseline

```text
python3 scripts/governance_check.py --strict
Blockers: 0
```

### 9.3 Runtime Benchmark Baseline

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
| Historical R5 compliance not 100% | Legacy debt | changed-files strict enforcement |
| Full CI test suite not complete | Local validation required | `make docs-check`, network tests, diagnostics |
| Browser/private workflows require careful operation | Data leakage risk | MCP Guard, mode isolation, high-risk approval |

---

## 11. Engineering Design Generation Inputs

An AI generating a future `ENGINEERING_DESIGN.md` from this dossier and an architecture design should extract:

1. Repository structure and ownership boundaries from §2.
2. Current architecture layers from §4.
3. Capability inventory from §5.
4. Configuration SSOT from §6.
5. Runtime and model constraints from §7.
6. Commands and diagnostics from §8.
7. Validation evidence from §9.
8. Known limitations from §10.
9. Governance rules from `docs/adr/ADR-008-documentation-governance-automation.md`.
10. Runtime configuration rules from `docs/adr/ADR-009-local-model-runtime-configuration.md`.

The generated engineering design must not assume new infrastructure. It must preserve current module boundaries unless a new ADR explicitly changes them.

---

## 12. Suggested Future Extension Procedure

Before implementing any major new capability:

1. Read `HANDOFF.md`.
2. Read this dossier.
3. Read `docs/PROJECT_STATE.md`.
4. Read relevant ADRs.
5. Draft architecture/design first.
6. Add or update ADR if architecture or boundaries change.
7. Add tasks to `TASK_BACKLOG.md`.
8. Implement incrementally with tests.
9. Run `make docs-check`.
10. Update DEV_LOG / CHANGELOG / PROJECT_STATE.

---

## 13. Current Repository Health Summary

```text
Core FORGE: implemented and usable
Network Increment: finalized
Claude Code local model: usable
Local model runtime: centralized and benchmarked
Documentation governance: automated P2
Training docs: updated
MTP testing: concluded
Current state: ready for next design sprint
```

---

## 14. Final Notes

This V4 dossier is intentionally an asset-focused current-state record. It does not define or prescribe a new business system. Future engineering design should use this file as factual input and combine it with a separately approved architecture design.
