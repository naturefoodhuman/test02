<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 17:20:00
-->

# PROJECT_STATE —— 当前状态 SSOT

**更新日期**：2026-06-23 17:20 CST
**当前版本**：v1.3.0-dossier + Network Increment
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
- 根级 ADR：`docs/adr/ADR-001` ~ `ADR-007`。

---

## 3. Network Increment 已完成能力

### E3 / E4 Search + Extract

- SearXNG provider、models、cache、URL normalizer、domain scorer。
- Crawl4AI provider、ExtractorChain、Markdown cleaner、trafilatura fallback。
- Docker Compose：`docker/docker-compose.yml`，仅绑定本机端口。

### E5 Privacy Gateway

- InputSanitizer + prompt injection 防护。
- Unicode normalize。
- PII detector ABC / Presidio detector / Chinese recognizers / secret recognizers / common deterministic PII recognizers。
- SpaCyNERDetector。
- QwenPIIClassifier。
- PIIReplacer。
- encrypted PII Map DB。
- JSON Schema output validator。
- CanaryTokenMonitor。
- `PrivacyGateway` L1-L7 pipeline + `build_privacy_gateway()` factory。

### E2 MCP Guard

- pinned MCP install script。
- mcp-scan parser + scan scripts。
- schema hash validator。
- MCPGuard core abstraction。
- mode policy。
- high-risk approval。
- argument validator。
- PreToolUse hook。

### E6 Mode Profiles

- `.mcp.json.coding`
- `.mcp.json.research`
- `.mcp.json.private`
- `scripts/switch-mode.sh`

### E7 / E8 Browser

- Playwright MCP pinned metadata。
- PlaywrightMCPClient。
- PlaywrightOrchestrator。
- ProfileManager。
- AI-Public profile docs。
- SessionDetector。
- BrowserActionClassifier。
- restricted Playwright CLI wrapper。
- Chrome DevTools MCP pinned metadata。
- Private Chrome start script。
- AI-Private GitHub profile docs。
- ChromeDevToolsMCPClient。
- PrivateAccessPipeline。

### E9 Local RAG

- SQLite schema。
- BGE_M3_Embedder wrapper。
- RAGStore CRUD / chunking / raw_hash dedup。
- KNN search fallback using Python cosine similarity。

### E10 Ops

- `scripts/health-check.sh`
- `scripts/backup.sh`
- launchd plist for health and weekly mcp-scan。

### E11 Security Tests

- Prompt injection tests。
- PII bypass tests。
- Cookie leak tests。
- Canary E2E tests。

---

## 4. 当前测试基线

最近完整基线：

```bash
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 347 passed, 2 skipped, 44 warnings
```

说明：

- `2 skipped`：当前沙箱缺少 `presidio_analyzer`，Presidio 真实行为测试在最小环境中跳过。
- warnings 主要来自既有 `datetime.utcnow` deprecation warning。
- 真机服务验证需用户 Mac 环境。

---

## 5. 需要真机验证的项目

1. Docker services：SearXNG + Crawl4AI。
2. Ollama models：`qwen3:8b`、`bge-m3`。
3. MCP install + `mcp-scan`。
4. Chrome DevTools MCP + AI-Private Chrome。
5. Playwright MCP real browser flow。
6. launchd `launchctl load`。
7. RAG real bge-m3 embedding。

---

## 6. 当前下一步候选

推荐候选：

1. NetworkWorkflow / CLI 集成：把 search → extract → sanitize → privacy → RAG 串成命令入口。
2. 真机验证批次：Docker、Ollama、MCP、Chrome、Playwright、launchd。
3. 文档治理持续修复：保持 README / HANDOFF / PROJECT_STATE / TASK_BACKLOG 一致。
4. RAG 增强：sqlite-vec native KNN / reranker。

---

## 7. 文档状态

- `HANDOFF.md`：Agent 接手入口。
- `README.md`：人类快速入口。
- `TASK_BACKLOG.md`：§10 为任务状态唯一来源。
- `docs/DEV_LOG.md`：append-only 开发日志，顶部有最新索引。
- `docs/CHANGELOG.md`：append-only 变更摘要，顶部有最新索引。
- 架构基准：`NETWORK_ARCHITECTURE_FINAL.md`。
- 工程设计基准：`NETWORK_ENGINEERING_DESIGN.md`。

---

## 8. 过时资产策略

- `_obsolete/` 保持 `.gitignore` 忽略，不 push 到 GitHub。
- 旧诊断脚本统一放在 `scripts/diagnostics/`。
- 历史文档不作为当前状态依据，除非 README/HANDOFF/PROJECT_STATE 明确引用。
