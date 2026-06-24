<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-24 18:20:00
-->

# PROJECT_STATE —— 当前状态 SSOT

**更新日期**：2026-06-24 18:20 CST
**当前版本**：v1.4.0-dossier + Network Workflow MVP
**状态说明**：本文件是当前真实状态 SSOT；任务状态以 `TASK_BACKLOG.md` §10 为准。

---

## 1. 项目定位

FORGE Factory 是 AI 项目孵化工厂。当前主要开发对象是 `_infra/network/` 联网功能增量模块；`projects/debt-collection` 是试点/压测项目，不是当前主要开发目标。

---

## 2. Core FORGE 状态

已实现并保持有效：
- LangGraph HUB-SPOKE 多专家评审。
- 双文件模型管理：`config/models.yaml` + `config/routing_plans.yaml`。
- Smart Proxy SSE 流式网关。
- DataPrivacyGate + `config/privacy_policy.yaml`。
- KnowledgeHub / MemoryStore / compare-plans / retro。

---

## 3. Network Increment 已完成能力

### E12 Network Workflow (New!)
- **端到端搜索流**：已实现 `NetworkWorkflow` 类，串联 搜 -> 爬 -> 脱敏 -> 入库 全流程。
- **CLI 集成**：`python -m _infra.network.cli search` 已支持真机运行。
- **真机验证状态**：
    - ✅ SearXNG (8090) 通畅。
    - ✅ Crawl4AI (11235) 通畅，适配 0.9.x。
    - ✅ Ollama (11434) 通畅，支持 Qwen-14b 脱敏与 BGE-M3 向量化。
    - ⚠️ Google 连通性：受限于大陆网络环境，目前高度依赖 Clash 代理分流配置（需 ）。

### E3 / E4 Search + Extract
- SearXNG provider（适配 8090 端口）、Crawl4AI provider（适配 v0.9.x API）。
- 具备 `markdown_v2` 深度解析与 JSON 剥壳能力。

### E5 / E9 Privacy & RAG
- 7层隐私管线（Unicode -> Regex -> NER -> Qwen -> Replace -> Schema -> Canary）。
- SQLite RAGStore，支持超长文本截断（300 tokens/chunk）与 Ollama 8192 上下文。

---

## 4. 最新测试基线

**运行命令**：`python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q`
**结果**：`349 passed, 2 skipped, 44 warnings`
**说明**：2 skipped 为沙盒缺少 Presidio 环境；warnings 均为 datetime.utcnow 弃用警告，不影响业务。

---

## 5. 已知重大挑战

1. **代理隔离**：在大陆环境下，Docker 容器访问宿主机代理（Clash）存在物理隔阂，目前需配置 `host.docker.internal` 并关闭防火墙。
2. **数据一致性**：Crawl4AI API 频繁变动，需持续维护 `deep_clean_content` 解析函数。
