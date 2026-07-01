<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-01 00:00:00
-->

# PROJECT_DOSSIER_V4.md

**版本**：v1.4.10-dossier + Case Intelligence OS Readiness  
**生成日期**：2026-07-01  
**生成依据**：当前仓库源码、配置、维护文档、真机验证记录、治理报告、用户最新指令  
**性质**：当前状态卷宗 + 下一阶段升级准备文档  
**状态 SSOT**：当前状态仍以 `docs/PROJECT_STATE.md` 为准；任务状态以 `TASK_BACKLOG.md` §10 为准。

---

## 0. Executive Takeover Brief

FORGE Factory 当前已经从“AI 项目孵化工厂”升级为一个具备本地模型、联网检索、隐私网关、MCP 安全治理、浏览器自动化、本地 RAG、文档治理自动化和可追溯运行时配置的完整本地开发体系。

当前最新工作重点已经从联网功能实现转向：

```text
Case Intelligence Operating System（案件情报操作系统）升级准备
```

V4 卷宗的核心目标是为下一阶段升级建立清晰边界：哪些能力已具备、哪些组件可复用、哪些风险必须控制、哪些文档和配置是 SSOT、哪些能力需要作为 Case Intelligence OS 的基础层继续演进。

---

## 1. Current Project Identity

### 1.1 项目名称

FORGE Factory（AI 项目孵化工厂）

### 1.2 当前定位

FORGE Factory 是一个本地优先、可审计、可复用的 AI 项目孵化与智能工作流开发工厂。它通过五阶段流程、Agent/Skill 协作、本地/外部模型路由、联网搜索与提取、隐私网关、本地 RAG 和文档治理，把模糊需求转化为可运行、可测试、可交接的软件项目。

### 1.3 下一阶段定位

下一阶段目标是将 FORGE Factory 扩展为：

```text
Case Intelligence Operating System
```

即面向案件、争议、合规、证据、行动计划、风险评估、复盘沉淀的本地智能操作系统。

该系统不是单个“法律助手”，而是一个可复用的案件情报工作台：

```text
Case Intake → Evidence Ingestion → Entity/Timeline Extraction → Legal/Risk Review → Strategy Planning → Action Tracking → Audit/Retro
```

---

## 2. Current Version and Maturity

| 项 | 当前状态 |
|---|---|
| 当前版本 | v1.4.10-dossier + Case Intelligence OS Readiness |
| 核心工厂能力 | 已实现 |
| Network Increment | 已真机打通并收尾 |
| Claude Code for VS Code 本地模型接入 | 已打通 |
| 本地模型运行参数 SSOT | 已实现，见 `config/model_runtime.yaml` / ADR-009 |
| 文档治理自动化 | P2 已完成，见 ADR-008 |
| MTP / runtime benchmark | 已完成最终测试，保留诊断工具 |
| Case Intelligence OS | 尚未实现，当前为升级准备阶段 |

---

## 3. Major Current Capabilities

### 3.1 Core FORGE

- 五阶段生命周期：DISCOVERY → SPEC → BUILD → HARDEN → RETRO。
- HITL Gate：GATE-1 到 GATE-5。
- `forge` CLI：status / new / check / tasks / advance / gate / eval / compare-plans / retro。
- LangGraph HUB-SPOKE 多专家评审。
- 双文件模型管理：`config/models.yaml` + `config/routing_plans.yaml`。
- DataPrivacyGate + `config/privacy_policy.yaml`。
- MemoryStore + ModelRunRecord。
- KnowledgeHub / ChromaDB / LlamaIndex 体系。
- `_factory/skills`、`_agents`、`_factory/patterns`、`_factory/lessons`。

### 3.2 Network Increment

- SearXNG local search。
- Engine Matrix + per-engine Circuit Breaker。
- MultiSourceSearchOrchestrator。
- Tavily / Serper optional API fallback。
- Crawl4AI primary extraction。
- trafilatura bounded fallback。
- curl_cffi optional TLS fallback。
- Privacy Gateway L1-L7。
- SQLite Local RAG。
- Risk-control diagnostics。

### 3.3 Browser / MCP / Private Access

- Mode profiles：coding / research / private。
- MCP Guard：schema hash、mode policy、argument validator、high-risk approval、PreToolUse hook。
- Playwright public automation。
- Chrome DevTools private read-only pipeline。
- Cookie / localStorage / sessionStorage 拦截策略。

### 3.4 Claude Code for VS Code 本地模型接入

- VS Code Claude Code 使用 `ANTHROPIC_BASE_URL=http://localhost:4000`。
- Smart Proxy 将 Anthropic Messages API 转为本地 OpenAI-compatible backend。
- 常见 Claude Code UI 模型 alias 映射到本地模型。
- 支持 Anthropic SSE 包装。
- 已验证 `content_block_delta` 可输出。

### 3.5 Local Model Runtime

当前本地模型运行参数 SSOT：

```text
config/model_runtime.yaml
```

已纳入：

- MTPLX Qwen3.6 27B primary brain。
- MTPLX Gemma4 reviewer。
- llama.cpp Qwopus MTP GGUF reviewer。
- Ollama qwen3-coder-next。
- Ollama deepseek-r1:32b。
- Ollama Flash Attention / KV cache env。
- MTP / speculative decoding flags。
- runtime logs / memory estimates / kill patterns。

### 3.6 Documentation Governance

已落地：

- ADR-008：Documentation Governance Automation。
- ADR-009：Local Model Runtime Configuration SSOT。
- `scripts/governance_check.py --strict`。
- `make docs-check`。
- `make governance-check`。
- GitHub Actions governance workflow。
- pre-commit hook installer。
- launchd weekly governance check。
- `docs/DOCUMENT_INDEX.md` 自动生成。
- `docs/AGENT_HANDOFF_SUMMARY.md` 自动生成。

---

## 4. Architecture Snapshot

### 4.1 Current High-Level Architecture

```text
Claude Code for VS Code / Human Operator
        ↓
Smart Proxy 4000（Anthropic-compatible）
        ↓
LiteLLM / OpenAI-compatible local model endpoints
        ↓
MTPLX / Ollama / llama.cpp local models

Network Workflow:
User Query
  → InputSanitizer
  → MultiSourceSearchOrchestrator
  → SearXNG / API fallback
  → ExtractorChain
  → Privacy Gateway
  → Local RAG
  → CLI / Claude Code output

Factory Workflow:
DISCOVERY
  → SPEC / ADR / TASK_GRAPH / RISK
  → BUILD / TDD
  → HARDEN / Security Review
  → RETRO / Lessons / Patterns
```

### 4.2 Case Intelligence OS Candidate Architecture

```text
Case Intake
  → Case Schema Normalization
  → Evidence Import / Crawl / Manual Entry
  → Privacy Gateway / PII Mapping
  → Entity Extraction
  → Timeline Construction
  → Claim / Issue / Evidence Graph
  → Multi-Expert Review
  → Risk / Compliance / Strategy
  → Action Plan / Task Tracking
  → Audit Log / Retro / Lessons
```

### 4.3 Existing Components Reusable for Case Intelligence OS

| Case OS Capability | Existing FORGE Asset |
|---|---|
| Case intake | `projects/_TEMPLATE`, DISCOVERY, CHARTER |
| Evidence import | Network Search / Extract / Browser / Private pipeline |
| Privacy protection | Privacy Gateway, DataPrivacyGate, PII map DB |
| Entity extraction | Regex / Presidio / NER / Qwen classifier |
| Timeline | debt-collection timeline / acquisition patterns |
| Multi-expert reasoning | peer-review LangGraph pattern |
| Risk review | security-reviewer, compliance skills, risk-assessor expert |
| Local knowledge | Local RAG / KnowledgeHub / ChromaDB |
| Audit trail | audit_log, DEV_LOG, CHANGELOG, MemoryStore |
| Retrospective learning | RETRO, lessons, MemoryStore |
| Governance | ADR, DOCUMENT_INDEX, governance_check |

---

## 5. Current SSOT Map

| 事实类型 | SSOT |
|---|---|
| 当前项目状态 | `docs/PROJECT_STATE.md` |
| 任务状态 | `TASK_BACKLOG.md` §10 |
| Agent 接手 | `HANDOFF.md` |
| 联网架构 | `NETWORK_ARCHITECTURE_FINAL.md` |
| 联网工程设计 | `NETWORK_ENGINEERING_DESIGN.md` |
| 架构决策 | `docs/adr/README.md` + ADR files |
| 文档索引 | `docs/DOCUMENT_INDEX.md` |
| 新 Agent 摘要 | `docs/AGENT_HANDOFF_SUMMARY.md` |
| 本地模型运行参数 | `config/model_runtime.yaml` |
| 模型清单 | `config/models.yaml` |
| 模型路由计划 | `config/routing_plans.yaml` |
| 隐私策略 | `config/privacy_policy.yaml` |
| 联网配置 | `config/network.yaml` |
| 开发流水 | `docs/DEV_LOG.md` |
| 需求变更 | `docs/CHANGELOG.md` |

---

## 6. Evidence of Current Validation

### 6.1 Network Validation

- SearXNG healthy。
- Search JSON 返回正常。
- Tavily / Serper `.env` 自动加载正常。
- CLI 端到端 search 成功。
- 风控诊断完成。
- Engine Matrix 已按真机结果收敛。

### 6.2 Claude Code for VS Code Validation

- `curl /v1/messages` 已有 `content_block_delta`。
- VS Code Claude Code 新会话 `只回复 pong` 10 秒内返回。
- `@HANDOFF.md` 接手规则总结由 20 分钟无输出恢复到约 2 分钟输出。
- Smart Proxy alias / streaming / port cleanup 已完成。

### 6.3 Local Runtime / MTP Validation

已验证：

- 8080 Qwen：Sustained MTP runtime + native-MTP draft head。
- 8082 Gemma：assistant MTP drafter active。
- 8084 Qwopus：llama.cpp MTP context。
- Ollama env：`OLLAMA_FLASH_ATTENTION=1`、`OLLAMA_KV_CACHE_TYPE=q4_0`。
- Benchmark 产物：`diagnostics/local_runtime_benchmark/20260626_181952`。

最终 MTP 结论：

```text
默认主模型保留 MTP depth3；不默认启用 KV q8/q4；no-MTP 可作为 fast-interactive 候选。
```

### 6.4 Test Baseline

当前记录基线：

```text
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
358 passed, 3 skipped, 44 warnings
```

---

## 7. Risk Register for Next Phase

| 风险 | 严重度 | 当前缓解 |
|---|---|---|
| Case 数据含高度敏感 PII | 高 | Privacy Gateway / local_only / PII map DB |
| 私域页面读取泄露 cookie/session | 高 | Private mode + MCP Guard + storage deny |
| 外部搜索结果污染 | 中高 | Search scoring / sanitizer / source citation |
| 搜索引擎风控 | 中 | Engine Matrix + Circuit Breaker + API fallback |
| 本地模型长上下文慢 / 卡住 | 中 | model_status / stop_local_models / prompt 分步策略 |
| 文档漂移 | 高 | governance_check / docs-check / ADR-008 |
| 本地模型参数不可追溯 | 中高 | model_runtime.yaml / ADR-009 |
| Case Intelligence OS 范围膨胀 | 高 | 下一阶段必须先出 SPEC / ADR / TASK_GRAPH |
| 医疗/法律安全误用 | 高 | 强制 disclaimer、HITL、审计日志、不可自动执行高风险建议 |

---

## 8. Case Intelligence OS Upgrade Readiness

### 8.1 Already Ready

- Local model runtime。
- Claude Code for VS Code local operation。
- Search / Extract / Privacy / RAG。
- Browser / Private access boundaries。
- Multi-expert LangGraph review。
- Document governance automation。
- Runtime benchmark / diagnostics。
- Training documentation。

### 8.2 Needs Design Before Build

以下内容在开始开发前必须先设计，不应直接编码：

1. Case data model。
2. Evidence object model。
3. Entity schema。
4. Timeline schema。
5. Claim / issue / evidence graph。
6. Case privacy policy。
7. Source provenance rules。
8. Human approval workflow。
9. Safety disclaimer and non-legal-advice boundary。
10. Case audit log / reproducibility rules。

### 8.3 Recommended First Epic

建议下一阶段第一 Epic：

```text
E13 Case Intelligence OS Foundations
```

建议 capabilities：

| Capability | 内容 |
|---|---|
| E13-C1 Case Schema | case_id, parties, facts, issues, evidence refs |
| E13-C2 Evidence Store | source, hash, provenance, extraction method |
| E13-C3 Timeline Builder | date normalization, event extraction, confidence |
| E13-C4 Entity Graph | people, orgs, locations, claims, obligations |
| E13-C5 Privacy Layer | per-case PII map and redaction policies |
| E13-C6 Case Review Workflow | multi-expert review nodes |
| E13-C7 Action Plan | tasks, deadlines, risks, human approvals |
| E13-C8 Case Audit | immutable logs, citations, reproducible reports |

---

## 9. Recommended Next Step

下一轮不建议直接写 Case Intelligence OS 代码。建议先执行：

```text
Case Intelligence OS SPEC Sprint
```

输出：

1. `CASE_INTELLIGENCE_ARCHITECTURE.md`
2. `CASE_INTELLIGENCE_ENGINEERING_DESIGN.md`
3. `TASK_BACKLOG.md` E13 section
4. ADR-010: Case Intelligence OS Data Model and Safety Boundary
5. Minimal demo case fixture
6. Acceptance criteria and test matrix

---

## 10. File / Module Areas to Watch

| Area | 注意事项 |
|---|---|
| `_infra/network/privacy_gateway` | Case OS 必须复用，不得绕过 |
| `_infra/network/local_rag` | Evidence / case chunks 可复用，但需 provenance 增强 |
| `_factory/patterns/peer-review` | Case review workflow 可复用，但可能需要 case-specific nodes |
| `projects/debt-collection` | 可作为试点参考，不应直接等同 Case OS |
| `config/model_runtime.yaml` | 本地模型性能/参数 SSOT，需保持可追溯 |
| `docs/adr` | 新 Case OS 重大决策必须新增 ADR |
| `docs/DOCUMENT_INDEX.md` | 新文档必须分类清晰 |

---

## 11. Current Known Limitations

- 无生产部署拓扑，仍是本地 Mac 工作站体系。
- CI 已有 governance workflow，但不是完整测试 CI。
- 本地模型工具调用能力仍弱于官方 Claude。
- MTPLX 后端真 token-by-token streaming 未完全证明；Smart Proxy 层已可输出 Anthropic SSE。
- Search scraping 类引擎在数据中心/代理 IP 下仍不可根治。
- Historical R5 header compliance 未达到 100%，采用 changed-files 阻断策略逐步治理。
- Case Intelligence OS 尚未有正式数据模型和安全边界 ADR。

---

## 12. Handoff Summary for Next Agent

下一任 Agent 必须：

1. 先读 `HANDOFF.md`。
2. 再读 `docs/PROJECT_STATE.md`。
3. 再读 `TASK_BACKLOG.md` §10。
4. 再读 `docs/DOCUMENT_INDEX.md`。
5. 再读本文件。
6. 不要直接改 Case OS 代码。
7. 先产出 Case Intelligence OS 架构/工程设计/ADR。
8. 所有用户操作指令集中放在回复最后的“操作区”。

---

## 13. Current Repository Health Summary

```text
Core FORGE: usable
Network Increment: finalized
Claude Code local model: usable
Local model runtime config: centralized
Documentation governance: automated P2
MTP benchmark: concluded
Training docs: updated
Case Intelligence OS: ready for design sprint, not yet implemented
```

---

## 14. Final Recommendation

FORGE Factory 已具备进入 Case Intelligence OS 升级的工程基础。下一步的关键不是继续堆功能，而是先锁定：

```text
Case 数据模型 + Evidence provenance + Privacy boundary + Human approval workflow
```

这些必须先有 ADR 和 SPEC，再进入实现。
