# Project Dossier V3

**版本**: v1.3.0-dossier (Current State)  
**生成日期**: 2026-06-21 (基于仓库真实状态)  
**生成依据**: 完整仓库扫描（Repository Scan / Source Code Scan / Configuration Scan / Database Scan / Infrastructure Scan / CI/CD Scan / Documentation Scan）  
**原则遵守**: Reality Over Assumptions · Current State Only · Code Is Source Of Truth · Evidence Driven · Future-Agent Friendly  

---

## 1. Executive Summary

### Project Name
FORGE Factory（AI 项目孵化工厂）

### One-Line Description
Mac M1 Max 64G 单机上将“模糊想法”通过五阶段工作流（DISCOVERY → SPEC → BUILD → HARDEN → RETRO）+ LangGraph 多专家评审引擎 + 双文件模型配置，重复、可重复地转化为可运行 AI 软件项目的脚手架 + 知识库 + CLI 体系。

### Three-Sentence Description
FORGE Factory 是一个面向独立开发者和架构师的 AI 项目孵化工厂，不是单一软件，而是由 _infra、_factory、projects 组成的完整工作体系。  
核心实现包括：基于 LangGraph 1.0 的 HUB-SPOKE 评审图（primary_expert + 多个 reviewer 并行）、双文件模型管理（config/models.yaml + config/routing_plans.yaml）、DataPrivacyGate + privacy_policy.yaml 数据出境策略执行器、Smart Proxy 流式网关（SSE + 自动 MTPLX 拉起 + 600s chunk 超时）。  
当前真实状态为 v1.3.0-dossier，已完成工厂级 7 个 ADR（ADR-001~007）、LangGraph 完整迁移（去 Agno）、真实模型调用（1132s 共识报告）、MemoryStore 运行记录 + forge eval/compare-plans 能力；无 CI/CD、无容器化、无生产部署拓扑。

### Elevator Pitch
在单机 Mac M1 Max 64GB 环境下，任何人（含 AI Agent）5 分钟内即可接手，通过 forge CLI + 5 阶段 + HITL Gate + 真实 LangGraph 评审，把法律/债务/合规类想法转化为带隐私门控、可回放、可对比的多专家共识报告系统。

### Current Maturity Assessment
- **成熟度等级**: v1.3.0-dossier（已完成架构治理 + 核心执行引擎落地）
- **核心能力已实现**: LangGraph 评审引擎（HUB-SPOKE + HITL + Memory）、双文件路由引擎、DataPrivacyGate、Smart Proxy Streaming、forge CLI 五阶段驱动、KnowledgeHub（ChromaDB + LlamaIndex）
- **缺失/未实现**: CI/CD（无 .github/workflows）、容器化（无 Dockerfile）、前端（无）、生产部署（纯本地 Mac）、完整测试覆盖（<15% 提及于审计）
- **Evidence**:
  - `docs/PROJECT_STATE.md`（v1.3.0-dossier）
  - `HANDOFF.md`（v1.3.0）
  - `docs/adr/README.md` + 7 个 ADR
  - `CHANGELOG.md`（第 44 轮 + 真实模型调用里程碑）
  - `config/routing_plans.yaml`（active_plan: full-check + 5 plans）
  - `git log --oneline -5`

---

## 2. Business Context

### Problem Being Solved
从“模糊想法”到“能跑的 AI 软件项目”的过程重复、低效、不可复现；缺乏统一的脚手架、配置驱动路由、隐私策略执行、多专家评审闭环，导致单人/Agent 难以持续孵化高质量项目。

### Target Users
- 独立开发者 / 架构师（Mac M1 Max 环境）
- AI Agent（未来接手者）
- 项目接管者（需 5 分钟建立认知）

### Core Value Proposition
- **配置驱动而非代码驱动**：双文件模型管理 + routing_plans.yaml 一键切换方案
- **隐私可控**：privacy_policy.yaml + DataPrivacyGate（local_only / human_approve / mask_then_allow / allow）
- **可复现 + 可审计**：LangGraph checkpointer + MemoryStore + forge compare-plans
- **知识复用**：_factory/experts + KnowledgeHub + lessons

### Major Use Cases
1. debt-collection 试点（个人合法讨债助手）：debt add → debt intel → debt review（LangGraph 多专家评审）→ debt report
2. 多方案 A/B 测试：forge compare-plans --days 30（基于 MemoryStore）
3. 新项目孵化：forge new <name> --domain legal → forge status / check / advance
4. 真实 LLM 共识生成：Smart Proxy (4000) + MTPLX 后端（1132s 真实报告已验证）

**Evidence**:
- `projects/debt-collection/src/debt/cli.py`（debt review / cmd_review）
- `_factory/patterns/peer-review/src/peer_review/graph/execution.py`（run_langgraph_review）
- `config/routing_plans.yaml`
- `docs/PROJECT_STATE.md` §4

---

## 3. Current Status

### Development Status
- **当前版本**: v1.3.0-dossier
- **分支**: main（干净工作树）
- **治理状态**: Phase 1（Documentation Governance）已完成（7 个工厂级 ADR 创建、HANDOFF 清理、PROJECT_STATE 去重）

### Implemented Features

#### 已实现（按模块）
- **Peer-Review 核心引擎**（_factory/patterns/peer-review）：
  - LangGraph 1.0 HUB-SPOKE 评审图（primary_expert + reviewer_* 并行 + consensus + decision + human_review_gate + record_run）
  - RoutingPlanEngine（双文件加载 + active_plan 切换 + 内存安全检查）
  - KnowledgeHub（ChromaDB + LlamaIndex + 版本去重）
  - DataPrivacyGate（策略驱动 + human_approve 显式 yes 确认）
  - MemoryStore + ModelRunRecord（运行记录 + 方案对比 SSOT）
  - LLMBackend 工厂（MTPLX / Ollama / LiteLLM / LlamaCpp + _ensure_server_running）
- **Smart Proxy**：
  - v5.0 SSE 流式直通（字段白名单 + 心跳保活 + 600s chunk 超时 + AppleScript 自动拉起 MTPLX）
- **forge CLI**（_infra/forge_tools）：
  - status / new / check / tasks / advance / gate / compare-plans / eval / retro（含 AI 辅助）
- **debt-collection 试点**：
  - 完整 ledger / intel / timeline / compliance / strategy / acquire
  - debt review（LangGraph 调用 + 隐私门控）
- **配置体系**：
  - models.yaml（A 文件）+ routing_plans.yaml（B 文件）+ privacy_policy.yaml
  - Pydantic schemas + load_all_configs 交叉验证
- **基础设施**：
  - _infra/setup.sh（7 步自检）
  - 5 个专家模板 + 知识库
  - _factory/lessons / skills

#### 部分实现
- forge eval / retro（CLI 骨架存在，真实数据依赖 runtime/memory.db）
- 项目状态检测（_detect_phase 基于文件存在性，粗略）
- 自动模型拉起（仅 MTPLX 8080/8082 + Ollama 11434）

#### 未发现实现
- CI/CD（无 .github、workflow、Dockerfile）
- 容器化 / 生产部署
- 前端 UI
- 多租户 / 区域化知识库
- 完整覆盖率测试（verify_architecture.py + 部分 pytest）
- 显存 LRU 自动实现（仅 Smart Proxy + 手动 purge_vram.sh）

### Feature Coverage Matrix

| Feature                  | Status     | Evidence |
|--------------------------|------------|----------|
| LangGraph HUB-SPOKE 评审 | 已实现     | `_factory/patterns/peer-review/src/peer_review/graph/review_graph.py` + `execution.py` |
| 双文件模型管理           | 已实现     | `config/models.yaml` + `config/routing_plans.yaml` + `RoutingPlanEngine` |
| DataPrivacyGate          | 已实现     | `config/privacy_policy.yaml` + `DataPrivacyGate` |
| Smart Proxy Streaming    | 已实现     | `_infra/smart_proxy_streaming.py` (v5.0) |
| forge CLI 五阶段         | 已实现     | `_infra/forge_tools/src/forge/cli.py` |
| MemoryStore / compare-plans | 已实现 | `peer_review/platform/memory_store.py` + `forge compare-plans` |
| KnowledgeHub (Chroma+LlamaIndex) | 已实现 | `KnowledgeHub` |
| debt-collection 完整功能 | 已实现     | `projects/debt-collection/src/debt/cli.py` |
| CI/CD                    | 未发现     | 无 .github/workflows |
| 容器化                   | 未发现     | 无 Dockerfile |
| 生产部署拓扑             | 未发现     | 纯 Mac 本地 |

### Known Limitations
- 仅记录代码/文档中明确存在的限制：
  - VRAM 红线 54GB（统一内存），超过自动 pkill（Smart Proxy LRU 描述）
  - chunk 超时 600s + 总时长 4h（针对长思考模型）
  - 无 CI（测试覆盖低）
  - 模型服务按需拉起依赖 AppleScript（仅 macOS）
  - runtime/ 目录为本地数据（.gitignore）
  - 部分旧 orchestrator.py 仍作为兼容层保留

**Evidence**:
- `docs/PROJECT_STATE.md` §5（待办 P0）
- `HANDOFF.md` §4（显存管理规则 R11）
- `DOCUMENT_AUDIT_REPORT.md`
- `config/routing_plans.yaml`
- `llm_client.py`（SERVER_COMMANDS + _ensure_server_running）

---

## 4. System Architecture

### High-Level Architecture
**本地 Mac 单机 + 网关 + 图执行引擎 + 多后端模型**

```
用户 / Claude Code
        ↓
Smart Proxy (4000, SSE)  ←→ LiteLLM (4000) 或 直接 MTPLX (8080/8082)
        ↓
forge CLI / debt CLI
        ↓
LangGraph Review Graph (HUB-SPOKE)
        ├── primary_expert (mtplx-qwen36-27b)
        ├── reviewer_* (并行/顺序)
        ├── consensus_builder
        ├── decision_engine
        └── human_review_gate (HITL) → MemoryStore
        ↓
KnowledgeHub (ChromaDB + LlamaIndex)
DataPrivacyGate (privacy_policy.yaml)
        ↓
本地模型 (MTPLX / Ollama / llama.cpp) / 外部 API (DeepSeek)
```

### Architectural Style
- **配置驱动 + 图执行**：双文件模型 + LangGraph StateGraph
- **HUB-SPOKE 并行**：Send() 信息隔离
- **策略即数据**：privacy_policy.yaml + DataPrivacyGate
- **平台层抽象**：RoutingPlanEngine / KnowledgeHub / MemoryStore

### Major Components
- **执行层**：peer_review.graph.* + execution.py
- **平台层**：RoutingPlanEngine, KnowledgeHub, DataPrivacyGate, MemoryStore
- **网关层**：smart_proxy_streaming.py + litellm-config.yaml
- **CLI 层**：forge CLI + debt CLI
- **数据层**：debt.db (SQLite), memory.db (SQLite), runtime/chroma_data

### Module Boundaries
- `_infra`：基础设施（代理、启动、自检）
- `_factory/patterns/peer-review`：核心可复用引擎（平台 + 图）
- `projects/*`：具体业务试点（debt-collection 为主）
- `config/`：SSOT 配置（A/B 文件 + 隐私）
- `docs/adr/`：工厂级决策记录

### Data Flow
1. debt review → 提取 privacy_fields → DataPrivacyGate.check
2. run_langgraph_review → RoutingPlanEngine → build_review_graph
3. primary_expert → Send() → reviewers（并行）→ consensus
4. LLM 调用 → llm_client.chat（BackendFactory + privacy_context）
5. 结果 → MemoryStore.record_run

### Control Flow
- 入口：debt cli / forge cli
- 核心：LangGraph invoke（带 checkpointer + interrupt_before）
- 模型调度：RoutingPlanEngine.get_model_for_node
- 隐私：DataPrivacyGate 在 CLI 层 + llm_client 层双重执行

### Integration Points
- Smart Proxy ↔ MTPLX (8080/8082) / Ollama (11434)
- LangGraph ↔ LiteLLM (4000) / 直接后端
- MemoryStore ↔ forge compare-plans / retro
- KnowledgeHub ↔ expert/*.expert/knowledge

### Dependency Relationships
- peer-review 依赖：langgraph, litellm, chromadb, pydantic, rich, ollama
- debt-collection 复用 peer-review 平台层
- forge CLI 动态 import peer-review

**Evidence**:
- `_factory/patterns/peer-review/src/peer_review/graph/review_graph.py`
- `llm_client.py`（BackendFactory + _privacy_check）
- `execution.py`
- `routing_plan_engine.py`
- `data_privacy_gate.py`

---

## 5. Technology Stack

### Frontend
- **Not Found** / 无前端实现

### Backend
- Python 3.11+
- LangGraph 1.0+（StateGraph + Send + SqliteSaver）
- FastAPI + uvicorn（Smart Proxy）
- Pydantic v2（配置 schemas）

### Database
- SQLite（debt.db、memory.db、langgraph checkpointer）
- ChromaDB（向量存储，persist_dir=runtime/chroma_data）

### Cache
- **Not Found**（仅内存缓存 + Chroma 持久化）

### Queue
- **Not Found**

### AI Stack
- **模型后端**：
  - MTPLX（主大脑 Qwen3.6-27B / Gemma4，端口 8080/8082）
  - Ollama（local-deepseek-r1:32b，11434）
  - llama.cpp（qwopus-35b，8084）
  - LiteLLM 网关（4000，统一入口）
- **Embedding**：Ollama bge-m3（默认）
- **路由**：RoutingPlanEngine + routing_plans.yaml
- **知识**：LlamaIndex + ChromaVectorStore
- **LLM 客户端**：多 Backend 工厂（MTPLXBackend / OllamaBackend / LiteLLMBackend）

### Infrastructure
- macOS M1 Max（统一内存 64GB）
- AppleScript 自动拉起模型
- 脚本驱动：setup.sh、forge-start.sh、purge_vram.sh

### Deployment
- **当前**：纯本地 Mac 开发/运行
- **未发现**：Docker、k8s、生产部署

### CI/CD
- **未发现**：无 .github/workflows、无 GitHub Actions
- Makefile 提供 test / lint / release

### Monitoring / Observability
- **未发现**：无 OpenTelemetry
- 简单日志 + MemoryStore 运行记录
- Smart Proxy 结构化日志

**Evidence**:
- `config/models.yaml`
- `config/routing_plans.yaml`
- `_infra/litellm-config.yaml`
- `peer_review/pyproject.toml`
- `llm_client.py`
- `Makefile`

---

## 6. Repository Analysis

### Repository Structure
```
.
├── _infra/                  # 基础设施
│   ├── smart_proxy_streaming.py
│   ├── litellm-config.yaml
│   ├── setup.sh
│   └── forge_tools/         # forge CLI
├── _factory/                # 工厂知识库
│   ├── patterns/peer-review/  # 核心引擎（LangGraph）
│   ├── experts/
│   ├── skills/
│   └── lessons/
├── config/                  # SSOT 配置
│   ├── models.yaml
│   ├── routing_plans.yaml
│   └── privacy_policy.yaml
├── projects/                # 试点项目
│   ├── _TEMPLATE/
│   └── debt-collection/     # 主试点
├── docs/                    # 文档
│   ├── adr/                 # 工厂级 ADR（7 个）
│   ├── PROJECT_STATE.md
│   └── CHANGELOG.md
├── _agents/                 # 全局 Agent 定义
└── scripts/                 # 辅助脚本
```

### Important Directories
- `_factory/patterns/peer-review/src/peer_review/`（核心）
- `config/`（模型 & 路由 SSOT）
- `projects/debt-collection/src/debt/`（业务实现）
- `docs/adr/`（决策记录）

### Important Files
- `config/models.yaml`（A 文件）
- `config/routing_plans.yaml`（B 文件）
- `_infra/smart_proxy_streaming.py`
- `_factory/patterns/peer-review/src/peer_review/graph/execution.py`
- `projects/debt-collection/src/debt/cli.py`
- `HANDOFF.md`
- `docs/PROJECT_STATE.md`
- `docs/adr/README.md`

### Entry Points
- `debt`（项目脚本入口）
- `forge`（_infra/forge_tools）
- `python -m uvicorn`（Smart Proxy 4000）
- `bash _infra/setup.sh`

### Core Modules
- `peer_review.graph.review_graph`
- `peer_review.platform.*`
- `peer_review.llm_client`
- `forge.cli`
- `debt.cli`

### Runtime-Critical Components
- Smart Proxy (4000)
- MTPLX 后端 (8080/8082)
- RoutingPlanEngine + load_all_configs
- LangGraph checkpointer
- DataPrivacyGate

### Areas Requiring Special Attention
- 模型端口映射（MODEL_TO_PORT + REAL_ID_MAP）
- 隐私字段提取与 Gate 调用位置
- MemoryStore 记录路径
- 旧 orchestrator.py 兼容层

**Evidence**:
- `git ls-files`
- `docs/PROJECT_STATE.md`
- 各核心文件头部注释

---

## 7. Data Layer

### Data Sources
- 本地 SQLite（debt ledger + intel + MemoryStore）
- ChromaDB（专家知识向量）
- 配置文件（yaml）

### Database Schema Summary
**debt.db**（projects/debt-collection）：
- debts 表（id, debtor_name, amount, debtor_id, debtor_region, nature, stage, ...）
- intels 表（debt_id, content, source, credibility, ...）

**memory.db**（runtime/）：
- model_runs 表（run_id, case_hash, plan_id, models_used, total_time_seconds, divergence_score, ...）

**langgraph checkpointer**：
- checkpoints 表（thread_id, checkpoint, ...）

### Entity Relationships
- Debt 1:N Intel
- ModelRunRecord 按 plan_id / case_hash 聚合

### Storage Strategy
- 所有运行数据保存在 `runtime/`（本地）
- Chroma persist 到 `runtime/chroma_data`
- .gitignore 排除 runtime/（除非显式保留）

### Vector Database Design
- ChromaDB PersistentClient
- collection_name = expert_id
- metadata: knowledge_version（mtime+size hash）
- embedding: Ollama bge-m3

### Index Design
- 版本去重：_get_version() + metadata 比对
- 检索：VectorStoreIndex.as_retriever(similarity_top_k)

### Data Lifecycle
- 运行记录追加（MemoryStore）
- 知识库按版本重建/复用
- 备份脚本：backup.sh（runtime tar）

**Evidence**:
- `projects/debt-collection/src/debt/models.py`（推断）
- `peer_review/platform/memory_store.py`（ModelRunRecord）
- `KnowledgeHub._get_version`
- `config/privacy_policy.yaml`

---

## 8. AI Layer

### Models
- mtplx-qwen36-27b（主大脑，20GB）
- mtplx-gemma4（独立评审，16GB）
- qwopus-35b（深度评审，36GB）
- local-deepseek-r1（逻辑推理）
- deepseek-pro / deepseek-flash（API 增强）

### Embedding Models
- bge-m3（Ollama，默认）

### RAG Architecture
- KnowledgeHub：LlamaIndex VectorStoreIndex + Chroma
- 专家知识目录：_factory/experts/<id>.expert/knowledge
- 检索注入：search() 返回 top_k 片段

### Agent Architecture
- LangGraph StateGraph（ReviewState）
- HUB-SPOKE：primary_expert → Send(reviewer_*) → consensus
- 节点：primary_expert, reviewer_*, consensus_builder, decision_engine, human_review_gate, record_run
- HITL：interrupt_before=["human_review_gate"]

### Tool Architecture
- **Not Found**（无工具调用层，纯 LLM 节点）

### Prompt Architecture
- 节点内部 prompt（代码中）
- expert.yaml 中的 system_prompt
- 注入 skill.md

### Context Architecture
- ReviewState（case_context, reviewer_opinions, consensus, models_used, data_fields, privacy_approved 等）
- 知识检索结果注入

### Memory Architecture
- LangGraph SqliteSaver（checkpointer）
- MemoryStore（运行历史 + 方案对比）

**Evidence**:
- `graph/review_graph.py`
- `graph/state.py`（推断）
- `llm_client.py`
- `KnowledgeHub`
- `config/models.yaml` + `routing_plans.yaml`
- `ADR-001` ~ `ADR-007`

---

## 9. Infrastructure & Environment

### Development Environment
- macOS M1 Max 64GB
- Python 3.11 + uv
- Ollama + MTPLX + llama-server
- .venv
- VS Code + Claude Code

### Testing Environment
- 本地 pytest（peer-review + debt-collection）
- verify_architecture.py
- 沙箱 benchmark（Arena）

### Production Environment
- **未发现**（纯本地开发环境）

### Deployment Topology
- 单机本地（无分布式）
- 端口：4000（Proxy）、8080/8082（MTPLX）、11434（Ollama）、8084（llama.cpp）

### Hardware Requirements
- Apple Silicon（M1 Max 推荐）
- 统一内存 ≥ 48GB（VRAM 红线）

### System Constraints
- 仅 macOS（AppleScript）
- 无网络时依赖本地模型
- 模型冷启动时间长（需按需拉起）

### External Dependencies
- 外部 API（DeepSeek / GLM）需 Key
- 本地模型需手动/AppleScript 启动

**Evidence**:
- `_infra/setup.sh`
- `HANDOFF.md` §2
- `docs/PROJECT_STATE.md`
- `smart_proxy_streaming.py`

---

## 10. Dependency Map

| Dependency              | Purpose                          | Used By                          | Criticality | Evidence |
|-------------------------|----------------------------------|----------------------------------|-------------|----------|
| langgraph + checkpoint-sqlite | 核心图执行 + HITL 检查点        | peer-review graph / execution    | 高         | pyproject.toml, review_graph.py |
| litellm                 | 网关统一调用                     | Smart Proxy, llm_client          | 高         | litellm-config.yaml, llm_client |
| chromadb + llama-index  | 向量知识库                       | KnowledgeHub                     | 高         | KnowledgeHub.py, ADR-005 |
| pydantic                | 配置严格校验                     | schemas.py, RoutingPlanEngine    | 高         | config/schemas.py |
| rich                    | CLI 表格输出                     | forge cli, KnowledgeHub          | 中         | cli.py |
| ollama                  | 本地模型客户端 + embedding       | OllamaBackend, KnowledgeHub      | 中         | llm_client.py |
| fastapi + uvicorn       | Smart Proxy                      | smart_proxy_streaming.py         | 高         | smart_proxy_streaming.py |
| httpx                   | 流式 HTTP                        | LiteLLMBackend, Proxy            | 高         | llm_client.py, smart_proxy |

---

## 11. Security Architecture

### Authentication
- **未发现**（本地信任）
- MTPLX token：`mtplx-token`
- LiteLLM 环境变量 Key

### Authorization
- DataPrivacyGate 策略驱动（无角色）

### Secret Management
- .env（_infra/.env）
- 环境变量引用 ${DEEPSEEK_API_KEY}
- .gitignore 排除 .env

### Sensitive Data Locations
- `config/privacy_policy.yaml`（策略）
- 运行时：runtime/debt.db（真实姓名、金额、ID）
- evidence 字段

### Security Controls
- DataPrivacyGate.check()（local_only 阻断 + human_approve 显式 yes）
- 节点级 _privacy_check
- 脱敏规则（keep_first_6_last_4 等）
- 策略文件人工拥有（AI 不可修改）

### Security Assumptions Found In Code
- 所有数据默认 human_approve（未定义字段）
- 本地模型永远允许
- 人工确认必须输入 "yes"（区分大小写）

**Evidence**:
- `config/privacy_policy.yaml`
- `data_privacy_gate.py`
- `llm_client.py`（_privacy_check）
- `debt/cli.py`（cmd_review 隐私流程）
- `ADR-003`

---

## 12. Performance Characteristics

### Runtime Characteristics
- 真实长思考模型耗时：1132.5s（Qwen + Gemma）
- 流式 chunk 超时：600s（最终）
- 总时长限制：4h

### Resource Consumption Patterns
- MTPLX 主模型：~20GB
- 并行评审：需内存安全检查（RoutingPlanEngine）
- VRAM 红线：54GB（超过 pkill 最久未使用）

### Scalability Characteristics
- 单机本地（无水平扩展）
- 方案切换支持并行/顺序_isolated

### Caching Strategy
- Chroma 版本去重缓存
- KnowledgeHub 内存索引缓存
- LangGraph checkpointer

### Concurrency Model
- LangGraph 并行 Send()
- reviewer 信息隔离
- Smart Proxy asyncio + httpx

### Performance-Critical Paths
- Smart Proxy upstream_pump（SSE 直通）
- llm_client.chat（流式 + 超时）
- LangGraph invoke（多节点）
- KnowledgeHub.load_expert_knowledge（首次构建重）

**Evidence**:
- `smart_proxy_streaming.py`
- `llm_client.py`（CHUNK_IDLE_TIMEOUT）
- `routing_plan_engine.py`（check_parallel_memory_safety）
- `HANDOFF.md` §4
- `PROJECT_STATE.md` §4

---

## 13. Decision Log

| Decision | Context | Chosen Approach | Evidence |
|----------|---------|------------------|----------|
| 立即全面迁移到 LangGraph 1.0 | Agno 不稳定 + 需原生 HUB-SPOKE + checkpointer | 直接使用 LangGraph + 薄兼容层 | `docs/adr/ADR-001-langgraph-migration.md` |
| 双文件模型管理体系 | 模型频繁切换 + 需人类可读 | models.yaml（A）+ routing_plans.yaml（B）+ RoutingPlanEngine | `docs/adr/ADR-002-dual-file-model-management.md` + `config/*.yaml` |
| DataPrivacyGate + 策略文件 | 法律敏感数据出境管控 | privacy_policy.yaml（4 种策略）+ Gate 执行 + 显式 yes | `docs/adr/ADR-003-...md` + `config/privacy_policy.yaml` |
| MTPLX 作为主力本地后端 | 高性能本地推理 | 8080/8082 MTPLX + Smart Proxy 代理 | `docs/adr/ADR-004-...md` + `litellm-config.yaml` |
| KnowledgeHub 纯 LlamaIndex + ChromaDB | 去 Agno 依赖 | Chroma + LlamaIndex + 版本去重 | `docs/adr/ADR-005-...md` + `KnowledgeHub.py` |
| forge eval 作为 A/B 测试核心 | 方案对比需要历史数据 | MemoryStore + compare-plans | `docs/adr/ADR-006-...md` |
| MemoryStore 作为计划对比 SSOT | RETRO + 对比需要可审计记录 | SQLite 记录 + plan_id 聚合 | `docs/adr/ADR-007-...md` |

**Evidence 来源**：
- `docs/adr/` 全部 7 个 ADR
- `DOCUMENT_AUDIT_REPORT.md`
- `CHANGELOG.md`（第 37 轮治理 + 第 47 轮真实调用）

---

## 14. Documentation Consistency Report

### Missing Documentation
- 完整 CI/CD 说明（未实现）
- 生产部署指南（未实现）
- 详细 Schema 文档（仅代码注释）

### Outdated Documentation
- 早期 research/ 文档与当前 LangGraph + 双文件架构脱节（已部分清理）
- 旧 Agno 描述（已标记兼容层）

### Documentation-Code Mismatches
- 已通过 Phase 1 治理大幅修复（HANDOFF 清理、PROJECT_STATE 去重、ADR 建立）
- 当前以代码为准：`docs/adr/README.md` 声明为 SSOT
- 残留：部分 docs/ 提及旧 dossier_v2（已删除）

**Evidence**:
- `DOCUMENT_AUDIT_REPORT.md`（Phase 1 状态）
- `docs/adr/README.md`
- `HANDOFF.md`
- `CHANGELOG.md`（第 36/37/44 轮）

---

## 15. Quick Start For New Architect

### Read First（严格顺序）
1. `HANDOFF.md`（最高规则 + 接手 SOP）
2. `docs/adr/README.md` + 最新 ADR（工厂级决策）
3. `docs/PROJECT_STATE.md`（当前状态 SSOT）
4. `config/models.yaml` + `config/routing_plans.yaml`（模型 SSOT）
5. `_factory/patterns/peer-review/src/peer_review/graph/execution.py`（核心执行入口）

### Core Files To Understand
- `peer_review/graph/review_graph.py`
- `peer_review/platform/routing_plan_engine.py`
- `peer_review/llm_client.py`
- `peer_review/platform/data_privacy_gate.py`
- `projects/debt-collection/src/debt/cli.py`
- `_infra/smart_proxy_streaming.py`

### Critical Runtime Paths
- Smart Proxy 4000 → MTPLX 8080/8082
- debt review → DataPrivacyGate → run_langgraph_review → graph.invoke
- forge compare-plans → MemoryStore

### Architecture Entry Points
- `build_review_graph`
- `RoutingPlanEngine.__init__`
- `DataPrivacyGate.check`
- `run_langgraph_review`

### Recommended Reading Order
1. HANDOFF.md
2. docs/adr/README.md
3. config/ 三个 yaml
4. peer-review 平台层
5. graph/execution.py + review_graph.py
6. debt/cli.py（实际使用示例）
7. CHANGELOG.md（最近里程碑）

---