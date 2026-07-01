<!--
创建/修改该文件的LLM大模型：
创建时间（北京时间）：2026-06-25 00:00:00
-->

# HANDOFF —— Agent 接手入口

> 目标：任何新 Agent 在 5–10 分钟内建立当前项目心智，并能安全继续开发。

---

## 0. 必读顺序

1. `HANDOFF.md`（本文件）
2. `docs/PROJECT_STATE.md`（当前状态 SSOT）
3. `TASK_BACKLOG.md` §10（任务状态 SSOT）
4. `NETWORK_ARCHITECTURE_FINAL.md`（联网架构基准）
5. `NETWORK_ENGINEERING_DESIGN.md`（联网工程设计 + 实现映射）
6. `docs/DEV_LOG.md` 顶部 Latest Index + 最新一轮
7. `docs/CHANGELOG.md` 顶部 Latest Index + 最新一轮
8. `docs/adr/README.md`（工厂级 ADR）
9. 如需背景再读：`PROJECT_DOSSIER_V4.md`、`PROJECT_DOSSIER_V3.md`、`DOCUMENT_AUDIT_REPORT.md`、`docs/UPGRADE_COMPLETION.md`

---

## 1. 项目定位

FORGE Factory 是 AI 项目孵化工厂。

- `debt-collection` 是试点 / 压测项目，不是当前主要开发目标。
- 当前主要开发对象：`_infra/network/` 联网功能增量模块。
- 当前架构版本：`v1.4.10-dossier-current-assets`。

---

## 2. 当前真实状态（2026-06-23）

### Core FORGE 已有能力

- LangGraph HUB-SPOKE 多专家评审。
- 双文件模型管理：`config/models.yaml` + `config/routing_plans.yaml`。
- Smart Proxy SSE 流式网关。
- DataPrivacyGate + `config/privacy_policy.yaml`。
- MemoryStore / compare-plans / retro。

### Network Increment 已实现能力

- Search：SearXNG provider、URL normalizer、domain scoring、cache、Docker Compose。
- Extract：Crawl4AI provider、trafilatura fallback、markdown cleaner、extractor chain、Docker Compose。
- Privacy Gateway：InputSanitizer、Unicode normalize、PII detectors、secret recognizers、NER、Qwen classifier、PII replacer、PII map DB、schema validator、canary、L1-L7 pipeline、factory。
- MCP Guard：pinned install、mcp-scan parser、schema hash、mode policy、high-risk approval、argument validator、PreToolUse hook。
- Mode Profiles：`.mcp.json.coding` / `.mcp.json.research` / `.mcp.json.private`、`scripts/switch-mode.sh`。
- Browser：Playwright MCP metadata/client/orchestrator/profile/session/action classifier/CLI wrapper；Chrome DevTools private metadata/client/private pipeline。
- Local RAG：SQLite schema、BGE_M3 embedder wrapper、RAGStore CRUD、KNN fallback。
- Ops：health-check、backup、launchd plist。
- Security tests：prompt injection、PII bypass、cookie leak、canary E2E。

当前最新测试基线见：`docs/PROJECT_STATE.md`。

---

### ⚠️ 核心突破 (2026-06-24)
- 已打通 Mac 真机全链路：Search -> Extract -> Privacy -> RAG。
- 攻克了 0.9.0 解析黑洞和 500 上下文溢出问题。

### ⚠️ 搜索风控加固 (2026-06-25)
- 已按用户“附录 1”完成 Engine Matrix、per-engine Circuit Breaker、MultiSourceSearchOrchestrator、可选 Brave/Tavily/Serper API fallback 与诊断工具 v2。
- 当前 API fallback 仅在 `BRAVE_API_KEY` / `TAVILY_API_KEY` / `SERPER_API_KEY` 存在时加载；密钥不得提交。
- 用户真机已验证 `.env` 自动加载、SearXNG healthy、Tavily/Serper fallback loaded、端到端 search 成功。

### ✅ 培训文档收尾 (2026-06-25)
- 已重写 `docs/工厂使用手册.md`、`docs/全功能最小示例项目.md`、`docs/工厂能力覆盖检查.md`，并补充 Claude Code for VS Code 主工作流与高风险能力安全演示。
- 新用户培训入口已收敛为：使用手册 → mini-gratitude-control-tower 示例 → 能力覆盖矩阵。

### ✅ 文档治理自动化 (2026-06-25)
- 已新增 `docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`。
- 已升级 `scripts/governance_check.py --strict`，并在 Makefile 增加 `make docs-check` / `make governance-check`。
- 每轮提交前应运行 `make docs-check`，重大变更后运行 `make governance-check` 并提交报告。

### ✅ MTP / Runtime Benchmark 收尾 (2026-06-26)
- 已完成本地模型运行参数 SSOT：`config/model_runtime.yaml` + ADR-009。
- 已完成一键 benchmark 和最终分析：默认保留 MTP depth3，KV q8/q4 不进默认，no-MTP 仅作为 fast-interactive 候选。
- 已新增 `PROJECT_DOSSIER_V4.md`，作为当前项目资产卷宗。

## 3. 当前下一步候选

当前 Network MVP、Claude Code 本地模型接入、文档治理 P2、本地模型运行参数 SSOT 与 MTP benchmark 均已收尾。下一步建议：

1. **等待用户指定下一阶段架构目标**：未获明确目标前，不主动设计新业务系统。
2. **如进入新系统升级**：先产出架构方案、工程设计、ADR、backlog 与最小验证 fixture，再编码。
3. **实现前治理检查**：运行 `make docs-check`，确认 `PROJECT_DOSSIER_V4.md` 与 SSOT 文档一致。
4. **保持资产卷宗优先**：后续 AI 可基于 `PROJECT_DOSSIER_V4.md` + 用户批准的架构方案生成工程设计。

继续开发前先检查 `TASK_BACKLOG.md` §10，并阅读 `PROJECT_DOSSIER_V4.md`。

---

## 4. 

---

## 5. 

---

## 6. LLM 文件头留痕规则

本规则只针对 **LLM 生成或 LLM 修改的文件**，用于事故追溯和责任边界识别。

- LLM 新建或修改文件：必须更新文件头。
- 人类手写 / 手工维护的文件：不强制要求 LLM header，不得因缺少 LLM header 阻止用户提交或 Push。
- 治理脚本可以对缺少 LLM header 的 changed files 给出 warning，但不得作为 blocker；是否补 header 由“该文件是否由 LLM 生成/修改”决定。

Python / YAML / shell 示例：

```text
# 创建/修改该文件的LLM大模型：Gpt 5.5 pro
# 创建时间（北京时间）：2026-06-23 17:20:00
```

Markdown 示例：

```text
<!--
创建/修改该文件的LLM大模型：Gpt 5.5 pro
创建时间（北京时间）：2026-06-23 17:20:00
-->
```

JSON 文件不能写注释，使用 `_forge_trace` 字段。

**模型名称**：必须写当前实际使用的模型比如 `Gpt 5.5 pro`。

---

## 7. 常用命令

### Network 静态健康检查

```bash
scripts/health-check.sh --static
```

### Network 全量测试

```bash
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
```

### Docker 服务

```bash
cd docker
export SEARXNG_SECRET_KEY="replace-with-local-random-secret"
docker compose up -d
```

### MCP 模式切换

```bash
scripts/switch-mode.sh coding
scripts/switch-mode.sh research
scripts/switch-mode.sh private
scripts/switch-mode.sh current
```

### PreToolUse Hook 手动测试

```bash
echo '{"server_id":"searxng","tool_name":"search","args":{"query":"public"},"mode":"research"}' \
  | scripts/hooks/pre_tool_use.sh
```

### 备份

```bash
scripts/backup.sh --dry-run
scripts/backup.sh
```

### RAG DB 初始化

```bash
python _infra/network/scripts/init_rag_db.py --db runtime/rag.db
```

---

## 8. 真机验证清单

以下在沙箱无法完整验证，需用户 Mac 执行：

1. Docker SearXNG / Crawl4AI：
   ```bash
   cd docker
   docker compose up -d
   curl 'http://127.0.0.1:8080/search?q=test&format=json'
   curl 'http://127.0.0.1:11235/health'
   ```
2. Ollama 模型：
   ```bash
   ollama serve
   ollama pull qwen3:8b
   ollama pull bge-m3
   ```
3. MCP server 安装：
   ```bash
   _infra/network/scripts/install_mcp.sh <name> <repo-url> <commit>
   ```
4. Private Chrome：
   ```bash
   _infra/network/scripts/start_private_chrome.sh ai-private-github 9222
   ```
5. launchd：
   ```bash
   cp scripts/launchd/*.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.network-agent.health.plist
   launchctl load ~/Library/LaunchAgents/com.network-agent.mcp-scan.plist
   ```

---

## 9. 文档 SSOT

- 当前状态：`docs/PROJECT_STATE.md`
- 任务状态：`TASK_BACKLOG.md` §10
- 架构基准：`NETWORK_ARCHITECTURE_FINAL.md`
- 工程设计：`NETWORK_ENGINEERING_DESIGN.md`
- 决策记录：`docs/adr/`
- 开发流水：`docs/DEV_LOG.md`
- 变更摘要：`docs/CHANGELOG.md`

冲突时优先级：用户最新指令 → `HANDOFF.md` → `docs/PROJECT_STATE.md` → `TASK_BACKLOG.md` §10 → 架构/设计文档 → 历史日志。

---

## 10. 过时 / 历史资产规则

- `_obsolete/` 必须继续被 `.gitignore` 忽略，不 push 到 GitHub。
- 旧诊断脚本放在 `scripts/diagnostics/`。
- `scripts/diagnostics/` 中脚本不是主流程入口，使用前必须重新确认当前架构适配性。
- 不要把浏览器 profiles、cookies、session、password、payment 数据提交或备份。

---

## 11. 常见排障

| 现象 | 处理 |
|---|---|
| `presidio_analyzer` 缺失导致测试 skip | 这是当前沙箱预期；真机安装 Presidio 后可跑完整检测。 |
| Docker 命令不存在 | 当前沙箱预期；在用户 Mac 上验证 Docker compose。 |
| `.mcp.json` 已存在且不是 symlink | `scripts/switch-mode.sh` 会拒绝覆盖；人工备份/删除后再切换。 |
| Hook 返回 deny | 查看 JSON 中 `reason`，通常是 mode policy、argument validation、schema change 或 high-risk approval。 |
| health-check runtime 失败 | 确认 Docker 服务、Ollama、runtime DB 是否已启动/初始化。 |

---

## 12. 保姆级指令格式要求

给用户的每条操作指令必须包含：

1. 终端编号
2. 当前路径
3. 虚拟环境状态
4. 预期输出

额外要求：

- 操作指令必须集中放在回复最后的“操作区”，不要在解释过程中穿插命令。
- 先解释结论、原因、判断，再统一给命令。
- 禁止给模糊指令，如“你试试看”。
