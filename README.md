<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-25 00:00:00
-->

# FORGE Factory（AI 项目孵化工厂）

FORGE Factory 是在 macOS / 本地优先环境中，把“模糊想法”通过五阶段工作流、专家评审、配置化模型路由、隐私网关和联网取数能力，持续孵化为可运行 AI 软件项目的工程体系。

> 当前开发重点：FORGE Factory 主体 + `_infra/network/` 联网增量模块。
> 当前状态 SSOT：`docs/PROJECT_STATE.md`。
> 任务状态 SSOT：`TASK_BACKLOG.md` §10。

---

## 1. 当前主要能力

### Core FORGE
- LangGraph HUB-SPOKE 多专家评审引擎。
- 双文件模型管理：`config/models.yaml` + `config/routing_plans.yaml`。
- Smart Proxy SSE 流式网关。
- DataPrivacyGate + `config/privacy_policy.yaml`。
- MemoryStore / forge compare-plans / retro。

### Network Increment（`_infra/network/`）
已实现并有单元/安全测试覆盖：

- E3 Search：SearXNGProvider、URL normalizer、domain scorer、SearchCache、Docker Compose 配置。
- E4 Extract：Crawl4AIProvider、trafilatura fallback、Markdown cleaner、ExtractorChain、Docker Compose 配置。
- E5 Privacy Gateway：InputSanitizer、Unicode normalize、PII detectors、Presidio/regex/NER/Qwen classifier、PII replacer、PII map DB、JSON Schema、Canary、主管线与 factory。
- E2 MCP Guard：pinned install、mcp-scan parser、schema hash、mode policy、approval、argument validator、PreToolUse hook。
- E6 MCP Profiles：`.mcp.json.coding` / `.mcp.json.research` / `.mcp.json.private`、`scripts/switch-mode.sh`。
- E7/E8 Browser：Playwright client/orchestrator/profile/session/action/CLI wrapper，Chrome DevTools private client + private full-mode pipeline。
- E9 Local RAG：SQLite schema、BGE_M3 embedder wrapper、RAGStore CRUD、KNN fallback。
- E10 Ops：health-check、backup、launchd plist。
- E11 Security：prompt injection、PII bypass、cookie leak、canary E2E tests。

最新测试基线：`358 passed, 3 skipped, 44 warnings`；详见 `docs/PROJECT_STATE.md` 与 `docs/DEV_LOG.md` 顶部索引。

---

## 2. 快速命令

### 环境自检
```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
bash _infra/setup.sh --check
```

### Network 静态健康检查
```bash
scripts/health-check.sh --static
```

### Network 全量单元 + 安全测试
```bash
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
```

### Docker 服务（SearXNG + Crawl4AI）
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

### MCP Guard Hook 手动测试
```bash
echo '{"server_id":"searxng","tool_name":"search","args":{"query":"public"},"mode":"research"}' \
  | scripts/hooks/pre_tool_use.sh
```

### 备份
```bash
scripts/backup.sh --dry-run
scripts/backup.sh
```

---

## 3. 目录速览

```text
.
├── HANDOFF.md                         # Agent 接手入口 + SOP
├── PROJECT_DOSSIER_V3.md              # 项目卷宗 + Network Addendum
├── NETWORK_ARCHITECTURE_FINAL.md      # 联网架构基准
├── NETWORK_ENGINEERING_DESIGN.md      # 联网工程设计基准 + 实现映射
├── TASK_BACKLOG.md                    # 任务定义；§10 为状态 SSOT
├── config/                            # models/routing/privacy/network/mcp/mode/canary 配置
├── docker/                            # SearXNG + Crawl4AI 本地 Docker Compose
├── _infra/network/                    # 联网增量模块源码
│   ├── search/
│   ├── extract/
│   ├── input_sanitizer/
│   ├── privacy_gateway/
│   ├── mcp_guard/
│   ├── browser/
│   ├── local_rag/
│   ├── scripts/
│   └── tests/
├── _factory/                          # 工厂知识库、专家、patterns、skills
├── projects/                          # 试点/样例项目
├── scripts/                           # 运维、mode switch、hook、wrapper 等脚本
└── docs/                              # 状态、日志、ADR、研究资料、手册
```

---

## 4. 接手阅读顺序

任何新 Agent 接手必须先读：

1. `HANDOFF.md`
2. `docs/PROJECT_STATE.md`
3. `TASK_BACKLOG.md` §10
4. `NETWORK_ARCHITECTURE_FINAL.md`
5. `NETWORK_ENGINEERING_DESIGN.md`
6. `docs/DEV_LOG.md` 顶部 Latest Index + 最新一轮
7. `docs/CHANGELOG.md` 顶部 Latest Index + 最新一轮
8. `docs/adr/README.md`

历史/背景再读：

- `PROJECT_DOSSIER_V3.md`
- `DOCUMENT_AUDIT_REPORT.md`
- `docs/UPGRADE_COMPLETION.md`

---

## 5. 文档 SSOT 规则

- 当前项目状态：`docs/PROJECT_STATE.md`
- 当前任务状态：`TASK_BACKLOG.md` §10
- 架构基准：`NETWORK_ARCHITECTURE_FINAL.md`
- 工程设计基准：`NETWORK_ENGINEERING_DESIGN.md`
- 决策记录：`docs/adr/`
- 开发流水：`docs/DEV_LOG.md`
- 变更摘要：`docs/CHANGELOG.md`

如果文档冲突，优先级：用户最新指令 → `HANDOFF.md` → `docs/PROJECT_STATE.md` → `TASK_BACKLOG.md` §10 → 架构/设计文档 → 历史日志。

---

## 6. Obsolete / Legacy 策略

`_obsolete/` 必须保持 `.gitignore` 忽略，不 push 到 GitHub。
历史诊断脚本统一放入 `scripts/diagnostics/`，不作为主流程入口。

当前不删除历史文档；被标为历史参考的文档不得作为 Current State SSOT。


## 7. Network 搜索示例

本地 `.env` 会自动加载 Tavily / Serper 等 fallback key：

```bash
cp .env.example .env
# 编辑 .env 后执行：
python3 -m _infra.network.cli search "python langgraph state machine" --mode research
```

当前联网功能已完成真机验收：SearXNG healthy，Tavily/Serper fallback 自动加载，提取超时会快速 fallback 到 snippet。

## 8. 新用户培训入口

- 完整使用手册：`docs/工厂使用手册.md`
- 全功能最小示例：`docs/全功能最小示例项目.md`
- 能力覆盖矩阵：`docs/工厂能力覆盖检查.md`
