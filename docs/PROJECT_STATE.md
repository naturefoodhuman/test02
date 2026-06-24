<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-24 14:48:00
-->

# PROJECT_STATE —— 当前状态 SSOT

**更新日期**：2026-06-24 14:48 CST
**当前版本**：v1.4.0-dossier + Network Workflow MVP + Anti-Bot Risk Control
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

### E12 Network Workflow & Multi-Source Engines
- **端到端搜索流**：已实现 `NetworkWorkflow` 类，串联 搜 -> 爬 -> 脱敏 -> 入库 全流程，支持批量并发抓取（`extract_batch`）。
- **多源数据扩充**：SearXNG 容器（`docker/searxng/settings.yml`）与 `config/network.yaml` 已启用 `duckduckgo`、`bing`、`wikipedia`、`github`、`stackoverflow`、`arxiv` 引擎。
- **Google 风控隔离**：Google 引擎由于连续报 CAPTCHA 被默认禁用。`SearXNGProvider` 具备上游异常捕获与降级能力（触发 429/403/CAPTCHA 时规范抛出 `SearchRateLimited`）。
- **维基百科反爬突围**：`Crawl4AIProvider` 爬取 Wikipedia 等特殊结构页面时，自动注入拟真 User-Agent 头部特征与 Magic 模式，攻克了 HTTP 400 拦截与 JSON 剥壳异常。

### E3 / E4 Search + Extract
- SearXNG provider（适配 8090 端口）、Crawl4AI provider（适配 v0.9.x API）。
- 具备 `markdown_v2` 与 HTML 深度解析剥壳能力。

### E5 / E9 Privacy & RAG
- 7层隐私管线（Unicode -> Regex -> NER -> Qwen -> Replace -> Schema -> Canary）。
- SQLite RAGStore，支持超长文本分段与向量缓存一致性校验。

---

## 4. 最新测试基线

**运行命令**：`python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q`
**结果**：`349 passed, 2 skipped, 44 warnings`
**说明**：2 skipped 为沙盒缺少 Presidio 环境；warnings 均为 datetime.utcnow 弃用警告，不影响业务。全量单元与安全测试全部通过。

---

## 5. 已知重大挑战

1. **大陆代理拓扑隔离**：Docker 容器访问宿主机代理（Clash）需配置 `host.docker.internal` 桥接。Google 引擎在数据中心 IP 下风控极严，目前已收敛至多源非 Google 引擎矩阵。
2. **上游 API 结构漂移**：Crawl4AI 与 Ollama SDK 参数持续迭代，已通过层级递归清洗（`deep_clean_content`）与强约束类型校验保持调用链稳定。
