<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-21 16:45:00 CST
-->

# FORGE Factory — Architecture Document (v1.2.5)

## 1. 总体分层架构

```
[ 用户界面层 ] 
      |── Claude Code (CLI / VS Code Extension)
      └── forge CLI (Command Line Interface)

[ 智能中继层 (Smart Proxy) ] —— 端口 4000
      |── 协议转换 (Anthropic <-> OpenAI)
      |── 显存调度 (LRU Unloading, Max 48G)
      └── 自动拉起 (AppleScript Terminal Pop-up)

[ 模型推理层 ]
      |── 8080: MTPLX (Qwen 27B)
      |── 8082: MTPLX (Gemma 4)
      |── 8084: Llama-server (Qwopus 35B)
      └── 11434: Ollama (DeepSeek R1)

[ 业务执行层 ]
      └── LangGraph 1.0 (StateGraph HUB-SPOKE)
```

## 2. 核心组件说明

### 2.1 Smart Proxy (显存看门人)
- **位置**：`_infra/smart_proxy.py`
- **职责**：
  1. **双向翻译**：让 Claude Code (Anthropic 协议) 能无缝访问本地 Qwen (OpenAI 协议)。
  2. **显存管家**：计算 M1 Max 剩余内存，执行串行拉起和过期卸载。
  3. **按需拉起**：通过 AppleScript 自动在用户屏幕上弹窗启动模型，保证 100% 可见性。

### 2.2 Unified Models Registry
- **位置**：`config/models.yaml`
- **SSOT 原则**：所有本地模型的 `base_url` 统一指向 `localhost:4000`，强制经过网关调度。

### 2.3 Peer-Review Engine
- **位置**：`_factory/patterns/peer-review/`
- **核心逻辑**：基于 LangGraph 的多专家并行评审。通过 `llm_client.py` 调用网关。

## 3. 显存管理策略 (R11)
- **策略名**：LRU (Least Recently Used) Unloading
- **软限制**：48 GB
- **行为**：当 `Sum(Active_VRAM) + New_Model_VRAM > 48G` 时，强制发送 `pkill` 指令给最久未使用的后端进程。

## 4. 进化规则
- **不重复造轮子**：优先集成主流开源库 (LiteLLM, FastAPI, HTTPX)。
- **物理透明**：模型拉起必须通过 Terminal 窗口，不得在后台静默“装死”。




## 5. Obsolete Assets Boundary

`/_obsolete/` 属于 GitHub 仓库中的可追溯历史资产区，但**不属于当前运行架构**。它用于保存废弃实现、历史设计稿、一次性诊断脚本与诊断输出。

当前架构入口仍是：

- `_infra/smart_proxy.py` / `_infra/start-litellm.sh` / `scripts/forge-start.sh`
- `_factory/patterns/peer-review/src/peer_review/graph/execution.py`
- `config/models.yaml`、`config/routing_plans.yaml`、`config/privacy_policy.yaml`
- `projects/debt-collection/` 当前试点、`projects/_TEMPLATE/` 项目模板，以及用户明确要求保留 active 的 `projects/legal-bot/`、`projects/project-b/`、`retro-data-share/`

旧 Agno/orchestrator 大实现位于 `_obsolete/_factory/patterns/peer-review/src/peer_review/`，当前源码只保留一个兼容 shim，避免历史导入直接失败；新功能不得回流到旧实现。
