<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 17:20:00
-->

# 联网功能最终架构设计方案

---

## 文档元数据

| 属性 | 值 |
|---|---|
| 文档标题 | 本地开源模型联网功能最终架构设计方案 |
| 架构模式 | Local-First + MCP Guard + Search/Crawl/Browser 分层 + Privacy Gateway |
| 目标平台 | macOS · Apple M1 Max · 64GB |
| 主控系统 | Claude Code |
| 来源文档 | 本地开源模型联网功能最终架构裁决 |
| 上下文参考 | PROJECT_DOSSIER_V3.md (FORGE Factory 项目档案) |

---

## 0. Implementation Status Note（2026-06-23）

本文件是联网功能的**架构基准**，不是进度 SSOT。当前实现状态请以 `docs/PROJECT_STATE.md` 与 `TASK_BACKLOG.md` §10 为准。

当前落地原则：所有联网功能均作为现有 FORGE Factory 的增量模块实现，实际代码路径为 `_infra/network/`，配置路径为根 `config/`，Docker 配置路径为根 `docker/`。

---

## 1. 架构总述

### 1.1 一句话架构

Claude Code 作为主控；SearXNG 做本地搜索；Crawl4AI 做公开网页提取；Playwright 做低风险浏览器自动化；Chrome DevTools MCP 只用于私域已登录 Profile 与调试；所有外部内容必须经过 Input Sanitizer + Presidio/Regex/NER + 本地 Qwen PII 判定；MCP 不再裸连，而是经过版本锁定、扫描、权限分层、审计和高危工具拦截。

### 1.2 核心设计原则

1. **Local First**：免费、开源优先、本地可部署，不依赖持续付费 SaaS。
2. **模式隔离**：Claude Code 分为 Coding / Research / Private 三种模式，不得同一 session 同时拥有 shell + browser + private data。
3. **确定性安全优先**：安全边界由确定性规则（Regex / Presidio / allowlist）构建，本地模型仅做辅助复核，不作为唯一安全边界。
4. **Search First / Browser Last**：优先搜索，浏览器仅用于搜索和提取无法覆盖的场景。
5. **只读优先 + 人工确认**：写操作（发帖、下单、支付、删除等）必须人工审批。
6. **主模型永远不看原始私域数据**：先脱敏，再摘要，主模型只接收占位符替换后的内容。
7. **MCP 安全治理**：所有 MCP server 必须经过版本锁定、安全扫描、权限分层和审计。

---

## 2. 最终架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                    macOS · Apple M1 Max · 64GB                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Claude Code                               │  │
│  │                 主控 / 规划 / 综合推理                       │  │
│  │                                                              │  │
│  │  Mode A: Coding Mode                                         │  │
│  │    ✅ repo / git / tests / limited shell                      │  │
│  │    ❌ browser / search / private profile                      │  │
│  │                                                              │  │
│  │  Mode B: Research Mode                                       │  │
│  │    ✅ SearXNG / Crawl4AI / Playwright public                  │  │
│  │    ❌ arbitrary shell / private secrets                       │  │
│  │                                                              │  │
│  │  Mode C: Private Mode                                        │  │
│  │    ✅ Chrome DevTools MCP + AI-Private Profile                │  │
│  │    ✅ full Privacy Gateway                                    │  │
│  │    ❌ shell / public tool cross-call / auto-write              │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                          │                                         │
│                Claude native MCP + Hooks                           │
│                          │                                         │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │                      MCP Guard Layer                          │  │
│  │                                                              │  │
│  │  - mcp-scan admission                                        │  │
│  │  - pinned versions / commit hashes                           │  │
│  │  - tool schema diff                                          │  │
│  │  - PreToolUse policy hook                                    │  │
│  │  - high-risk tool approval                                   │  │
│  │  - SQLite audit log                                          │  │
│  └───────────────┬──────────────┬───────────────┬────────────────┘ │
│                  │              │               │                  │
│      ┌───────────▼──────┐ ┌─────▼────────┐ ┌────▼─────────────┐   │
│      │ Search Layer     │ │ Extract Layer│ │ Browser Layer     │   │
│      │                  │ │              │ │                  │   │
│      │ SearXNG Docker   │ │ Crawl4AI     │ │ Playwright MCP    │   │
│      │ 127.0.0.1:8080   │ │ Docker/MCP   │ │ Playwright CLI    │   │
│      │ JSON enabled     │ │ 127.0.0.1    │ │ restricted wrapper│   │
│      └───────────┬──────┘ └─────┬────────┘ └────┬─────────────┘   │
│                  │              │               │                  │
│                  └──────────────┴───────────────┘                  │
│                                 │                                  │
│                  ┌──────────────▼───────────────┐                  │
│                  │        Input Sanitizer        │                  │
│                  │ - HTML/script/style strip     │                  │
│                  │ - prompt injection markers    │                  │
│                  │ - max length                  │                  │
│                  │ - provenance tagging          │                  │
│                  └──────────────┬───────────────┘                  │
│                                 │                                  │
│                  ┌──────────────▼───────────────┐                  │
│                  │        Privacy Gateway        │                  │
│                  │                               │                  │
│                  │ L1 Unicode normalize          │                  │
│                  │ L2 Presidio + Regex           │                  │
│                  │ L3 spaCy/Stanza NER           │                  │
│                  │ L4 Qwen3 8B local classifier  │                  │
│                  │ L5 Placeholder replacement    │                  │
│                  │ L6 JSON Schema validation     │                  │
│                  │ L7 Canary token detection     │                  │
│                  └──────────────┬───────────────┘                  │
│                                 │                                  │
│                  ┌──────────────▼───────────────┐                  │
│                  │ Local Memory / RAG            │                  │
│                  │ SQLite + FTS5 + sqlite-vec    │                  │
│                  │ bge-m3 embeddings             │                  │
│                  │ optional reranker             │                  │
│                  └───────────────────────────────┘                  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Private Browser Side                                         │  │
│  │                                                              │  │
│  │ AI-Private Chrome Profile                                    │  │
│  │ - headed                                                     │  │
│  │ - manual login only                                          │  │
│  │ - no password manager                                        │  │
│  │ - no autofill/payment                                        │  │
│  │ - no extensions                                              │  │
│  │ - remote debugging only during task                          │  │
│  │                                                              │  │
│  │ Chrome DevTools MCP                                          │  │
│  │ - browser-url 127.0.0.1:9222                                 │  │
│  │ - no usage statistics                                        │  │
│  │ - no performance CrUX                                        │  │
│  │ - private mode only                                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. 组件清单与分阶段部署计划

**关键原则（与 FORGE Factory 对齐）**：
- 联网功能是**现有 FORGE Factory 的增量叠加模块**（`_infra/network` 子模块）。
- **严禁**创建独立新项目目录、独立 pyproject、顶级 src/forge_network 或覆盖现有结构。
- 所有 Docker / 配置 / runtime 均复用现有 FORGE 根目录。
- 实现时严格遵循 PROJECT_DOSSIER_V3 + HANDOFF 中的架构保护原则。

### 3.1 组件裁决总表

| 组件 | 最终裁决 |
|---|---|
| Claude Code 主控 | **保留** |
| 独立 MCP Router | **删除**，改为 MCP Guard / Hook / Policy 层 |
| SearXNG | **保留**，Primary Search |
| FireCrawl | **从核心删除**，降级为可选参考 |
| Crawl4AI | **提升为 Primary Crawl / Extract** |
| Chrome DevTools MCP | **保留**，仅限私域 Profile / DevTools 调试，不做公开抓取主力 |
| Playwright MCP | **保留**，作为 Browser Automation 主工具之一 |
| Playwright CLI | **保留**，仅在受限 Shell / wrapper 下使用 |
| AI-Private Chrome Profile | **强制保留** |
| Browserbase / Operator / ChatGPT Agent | **不得进入核心架构** |
| Privacy Gateway | **保留并重构为确定性优先** |
| Qwen3 PII 模型 | **8B Primary，14B/30B-A3B Optional** |
| mcp-scan | **Phase 1 必须项** |
| Docker per MCP server | **对搜索/抓取/MCP server 保留；浏览器不强制容器化** |
| OpenWebUI / Perplexica | **不进核心**，作为独立 UI / answer engine 备选 |
| Tavily | **仅手动启用的免费 SaaS fallback**，不得核心依赖 |

### 3.2 Phase 1：必须部署

| 优先级 | 组件 | 用途 |
|---:|---|---|
| 1 | Claude Code | 主控 |
| 2 | SearXNG Docker | 本地公开搜索 |
| 3 | Crawl4AI Docker / MCP | 网页提取 |
| 4 | mcp-scan | MCP 安全准入 |
| 5 | Privacy Gateway v1 | Regex / Presidio / 脱敏 |
| 6 | SQLite audit log | 工具调用审计 |
| 7 | Ollama + Qwen3 8B | PII 二分类 |
| 8 | `.mcp.json` mode profiles | 权限隔离 |

### 3.3 Phase 2：建议部署

| 优先级 | 组件 | 用途 |
|---:|---|---|
| 9 | Playwright MCP | 浏览器自动化 |
| 10 | Playwright CLI wrapper | 低 token 浏览器操作 |
| 11 | AI-Public Profile | 公开网页浏览 |
| 12 | AI-Private Chrome Profile | 私域访问 |
| 13 | Chrome DevTools MCP | 私域 / DevTools |
| 14 | Presidio custom recognizers | 中文 PII / token |
| 15 | Session expiry detector | 防封号 |
| 16 | macOS pf / container egress | 出站限制 |

### 3.4 Phase 3：高级增强

| 优先级 | 组件 | 用途 |
|---:|---|---|
| 17 | sqlite-vec + FTS5 RAG | 本地私域知识库 |
| 18 | bge-m3 embeddings | 多语言检索 |
| 19 | bge-reranker-v2-m3 | 检索重排 |
| 20 | Qwen3 14B / 30B-A3B MLX | 高质量本地摘要 |
| 21 | mcp-firewall / MCPProxy | 高级 MCP 中介 |
| 22 | Canary token monitor | 泄露检测 |
| 23 | launchd health supervisor | 自动恢复 |

---

## 4. Claude Code 主控与模式隔离

Claude Code 作为主控系统，支持 MCP server 添加、项目级 `.mcp.json`、user scope、local scope 等配置方式，支持 `claude mcp add`、`claude mcp list` 等管理方式，支持 hooks（如 `PreToolUse`）用于工具调用前安全检查。

Claude Code 不能同时拥有：私域网页读取权限、本地 shell / 文件写权限、未经过滤的外部网页内容。否则构成 confused deputy / prompt injection 风险。

必须通过 per-mode `.mcp.json` 将 Claude Code 分为以下三种模式：

### 4.1 Coding Mode

```
允许：
- repo read/write
- git
- tests
- shell（需审批）

禁止：
- browser MCP
- search MCP
- private profile
```

### 4.2 Research Mode

```
允许：
- SearXNG
- Crawl4AI
- Playwright public
- Privacy Gateway

禁止：
- arbitrary shell
- filesystem write outside tmp
- SSH keys
- private repo secrets
```

### 4.3 Private Mode

```
允许：
- Chrome DevTools MCP private profile
- Privacy Gateway full mode
- read-only extraction

禁止：
- shell
- public search cross-call
- write actions without approval
```

---

## 5. MCP 安全治理层（MCP Guard Layer）

### 5.1 架构设计

不使用通用 MCP Router 作为默认核心。采用以下结构替代：

```
Claude Code
→ mode-specific .mcp.json
→ pinned MCP servers
→ mcp-scan admission
→ PreToolUse policy hook
→ SQLite audit
```

MCP 生态的主要风险包括：tool poisoning、rug pull、tool schema mutation、MCP server supply-chain attack、跨 server tool confusion、prompt injection 经 tool description 进入模型上下文。

### 5.2 MCP Server 安装规则

**禁止：**

```bash
npx -y xxx@latest
uvx random-server
curl | sh
```

**允许：**

```bash
git clone <repo>
cd <repo>
git checkout <commit>
npm ci
npm audit
mcp-scan scan
```

配置中只写本地路径：

```json
{
  "mcpServers": {
    "searxng": {
      "command": "node",
      "args": [
        "/Users/YOU/ai-agent/mcp/searxng/dist/index.js"
      ]
    }
  }
}
```

### 5.3 mcp-scan 安全准入

Phase 1 必须部署。

```bash
pipx install mcp-scan
mcp-scan scan
mcp-scan whitelist tool searxng <HASH>
```

用途：

- tool poisoning 检测
- rug pull 检测
- tool schema hash pin
- secrets / PII 检测
- toxic flow 检测

### 5.4 工具安全策略

**Tool Confusion 防护：**

- 每个模式只加载最少 MCP server。
- 高危 server 不与 shell / filesystem 同时启用。
- tool names 加 namespace。
- tool schema hash pin。
- tool description diff。
- 新增 / 变更 tool 必须人工批准。

**MCP 注入防护：**

外部内容不能直接成为 tool 参数。所有参数先过：

```
URL allowlist
method allowlist
argument regex
secret detector
PII detector
max length
```

**Server 信任边界：**

- 不从 registry 直接盲装。
- 不用 `@latest`。
- 不用 `npx -y remote-package` 作为长期配置。
- clone → review → lock commit → local path。
- 依赖用 lockfile。
- 每周 `mcp-scan scan`。

---

## 6. 搜索层

### 6.1 Primary：SearXNG Docker

SearXNG 是免费、自托管、隐私导向的 metasearch engine，聚合多个搜索服务，用户不被 tracking / profiling，支持 HTTP Search API。JSON 输出必须在 `settings.yml` 中启用，否则请求 `format=json` 可能返回 403。

**部署方式：**

```bash
mkdir -p ~/ai-agent/searxng

# 重点：只绑定本机
ports:
  - "127.0.0.1:8080:8080"
```

**关键配置：**

```yaml
search:
  formats:
    - html
    - json

server:
  bind_address: "0.0.0.0"
  port: 8080
  secret_key: "REPLACE_WITH_LOCAL_RANDOM"

outgoing:
  request_timeout: 3.0
  max_request_timeout: 6.0
```

**Engine 策略：**

```
Primary engines:
- DuckDuckGo
- Brave（若无需付费 API 即可用）
- Bing
- Wikipedia
- GitHub
- StackOverflow
- arXiv
- MDN / docs（如适用）

Disable / cautious:
- Google（如频繁 CAPTCHA）
- 返回大量 SEO 噪声的 engine
```

### 6.2 搜索质量策略

```
Top 20 search results
→ canonical URL normalize
→ domain reputation scoring
→ official/docs/github/arxiv boost
→ spam domain denylist
→ fetch Top 5
→ rerank
→ only then return to agent
```

必须处理：

- 同 URL 多次出现
- SEO farm
- AI-generated spam
- GitHub / docs / arXiv / official docs 优先级
- 时间敏感查询
- 多语言查询
- query rewrite
- source diversity

### 6.3 搜索运维策略

SearXNG 聚合多个 engine，速度不稳定，且会被上游搜索引擎反爬 / CAPTCHA / 429 限流。

必须配置：

- engine timeout
- max result
- disabled engines
- health check
- cache
- fallback engine profile

运维策略：

- 不追求无限并发，维持单用户低速。
- engine health daily check。
- 失败时切换 engine profile。
- 必要时人工搜索。
- Tavily / Brave 只作为手动 emergency fallback。

### 6.4 Token 消耗控制

不要把搜索结果全部塞给主模型。

```
search result snippet ≤ 20 条
fetch page ≤ Top 5
每页 markdown ≤ 8k chars
long page → chunk + local rerank
private page → summary only
```

### 6.5 Fallback：Tavily

手动启用，不进核心。Tavily 当前有免费层和 API credits，但仍然是 SaaS API。

```
默认关闭
仅当 SearXNG 连续失败时人工启用
不得写入核心工作流
不得处理私域数据
不得处理 PII
```

### 6.6 不进核心的搜索工具

OpenWebUI Search / Perplexica / Vane 不进核心架构。用途仅限：

- 本地聊天 UI
- answer engine
- 非 Claude Code 的人类检索界面

OpenWebUI 支持多种 web search provider（包括 SearXNG、Tavily、Brave、Bing 等），但这属于 UI 平台能力，不应替代底层搜索管线。

---

## 7. 抓取 / 提取层

### 7.1 Primary：Crawl4AI

Crawl4AI 为 Apache-2.0 license，本地运行，适合 LLM-ready Markdown，支持 CLI、Docker。其 MCP server 支持 Claude Code，提供 SSE / WebSocket endpoint。

**部署方式：Docker server**

```bash
docker run -d \
  --name crawl4ai \
  -p 127.0.0.1:11235:11235 \
  --shm-size=1g \
  --restart unless-stopped \
  crawl4ai-local:latest
```

**Claude Code MCP 接入：**

```bash
claude mcp add --transport sse c4ai-sse http://127.0.0.1:11235/mcp/sse
```

**允许工具：**

```
允许：
- md
- html
- crawl（仅公开域名）
- screenshot（人工审批）
- pdf（人工审批）

默认禁用 / 人工确认：
- execute_js
```

**限制规则：**

- `execute_js` 默认禁用或人工确认。
- 不用于高风控登录站点。
- 不做 cookie / token / localStorage 提取。
- 不用于绕过网站访问控制。
- 对 JS-heavy SPA 失败时降级到 Playwright。

### 7.2 Secondary：trafilatura / readability-lxml

用于静态网页、新闻、blog、文档页、无 JS 页面。

优点：无浏览器、低内存、快速、攻击面小。

### 7.3 Fallback：Playwright

用于 JS-heavy SPA、登录后页面、需要点击展开的页面、Crawl4AI markdown 质量差的页面。

### 7.4 提取层角色分工

```
公开网页提取：      Crawl4AI Primary
静态网页快速提取：  trafilatura / readability-lxml Fallback
JS-heavy 页面：     Playwright Fallback
私域登录页面：      Chrome DevTools MCP / Playwright 专用 Profile，不走 Crawl4AI
```

---

## 8. 浏览器层

### 8.1 Browser Automation Primary：Playwright MCP

Playwright MCP 是 Microsoft 维护的 MCP server，使用 accessibility tree 而非 pixel-based input。适合公开站、测试、表单自动化。`--allowed-origins` 不能当作完整安全边界，真正的边界在 MCP Guard / hooks / profile / network。

**安装（禁止 @latest 进入长期配置）：**

```bash
npm view @playwright/mcp version

# 固定版本
npm install --prefix ~/ai-agent/mcp/playwright @playwright/mcp@<PINNED_VERSION>
```

**Claude Code 配置示例：**

```json
{
  "mcpServers": {
    "playwright-public": {
      "command": "node",
      "args": [
        "/Users/YOU/ai-agent/mcp/playwright/node_modules/@playwright/mcp/cli.js",
        "--browser=chromium",
        "--headed",
        "--user-data-dir=/Users/YOU/ai-agent/profiles/ai-public",
        "--blocked-origins=https://accounts.google.com;https://bank.example.com"
      ]
    }
  }
}
```

### 8.2 Browser CLI：Playwright CLI（受限 wrapper）

不允许 Claude Code 直接任意 Bash。必须通过受限 wrapper 调用：

```bash
claude → run_playwright_action.py → fixed allowlist → playwright CLI
```

**允许命令：**

```
open
snapshot
click by ref
type by ref
wait
close
```

**禁止命令：**

```
shell arbitrary
file read outside snapshot dir
network exfil
cookie export
storage export
```

Playwright CLI 比 MCP 更 token-efficient；MCP 更适合需要 persistent state、rich introspection、iterative reasoning 的场景。

### 8.3 Private Browser：Chrome DevTools MCP

Chrome DevTools MCP 会将浏览器实例内容暴露给 MCP client，使其能够 inspect、debug、modify 浏览器或 DevTools 中的数据。其 usage statistics 默认开启，可用 `--no-usage-statistics` 关闭。`--autoConnect` 支持连接本地运行的 Chrome 144+ 实例，也支持 `--browser-url=http://127.0.0.1:9222` 连接远程调试端口。

**安全警告：** 开启 remote debugging port 后，本机任意应用都可能连接并控制浏览器，因此 Chrome 要求使用非默认 user data dir。

**启动 AI-Private Chrome：**

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/ai-agent/profiles/ai-private-github" \
  --no-first-run \
  --no-default-browser-check \
  --disable-extensions
```

**MCP 配置：**

```json
{
  "mcpServers": {
    "chrome-devtools-private": {
      "command": "node",
      "args": [
        "/Users/YOU/ai-agent/mcp/chrome-devtools/node_modules/chrome-devtools-mcp/dist/index.js",
        "--browser-url=http://127.0.0.1:9222",
        "--no-usage-statistics",
        "--no-performance-crux"
      ]
    }
  }
}
```

**允许用途：**

1. 私域已登录 Profile 的只读访问
2. 网络请求 / console / performance 调试
3. Claude Code / VS Code 开发调试
4. Playwright 失败时的人工辅助

**禁止用途：**

- 大规模公开网页抓取
- 自动登录
- 下单 / 支付 / 发帖
- 读取 cookie / localStorage / sessionStorage
- 任意 JS eval
- 日常主 Chrome Profile

**强制规则：**

```
- 禁止日常主 Profile
- 禁止 password manager
- 禁止 autofill
- 禁止支付信息
- 禁止 extension
- 禁止 cookie/localStorage/sessionStorage 读取
- 私域写操作人工确认
- 任务结束关闭 remote debugging Chrome
```

### 8.4 浏览器 Profile 管理

必须维护三个 Profile 层级：

```
Daily Chrome Profile        # 人类日常使用，Agent 永不接触
AI-Public Profile           # 公开网页自动化
AI-Private Profile          # 私域已登录，只读优先
```

多账号管理建议：不在一个 Profile 登录多个敏感账号。

```
profiles/
  ai-private-github/
  ai-private-notion/
  ai-private-gmail-readonly/
  ai-private-shopping/
```

每个 profile 配置：

- allowed domain
- forbidden actions
- session expiry detector
- audit label

### 8.5 浏览器权限控制

禁止浏览器工具读取：

- cookie
- localStorage
- sessionStorage
- password manager
- autofill
- payment forms
- browser history
- extensions

### 8.6 浏览器崩溃恢复

必须记录：

- last URL
- task id
- profile name
- last safe snapshot
- whether write action pending

恢复规则：

```
read-only task    → 可自动重启
write task        → 不自动恢复，人工确认
payment/order/delete → 永不自动恢复
```

---

## 9. 输入净化层（Input Sanitizer）

所有来自搜索层、提取层、浏览器层的外部内容，在进入 Privacy Gateway 前必须经过 Input Sanitizer。

职责：

- HTML / script / style 标签剥离
- prompt injection 标记检测与移除（移除指令型段落）
- 最大长度限制
- provenance 标记（强制保留 source URL）
- 外部内容标记为 untrusted data
- Spotlighting / quote wrapping（帮助模型区分外部数据与指令）
- 不允许网页内容触发工具调用
- fetch 后先摘要为 facts，不保留指令语气

---

## 10. 隐私网关（Privacy Gateway）

### 10.1 设计原则

1. **确定性检测优先。**
2. **本地模型只能辅助，不是唯一安全边界。**
3. **先脱敏，再摘要。**
4. **主模型永远不看原始私域数据。**
5. **输出必须 JSON Schema 限制。**
6. **敏感原文只存在本地 encrypted SQLite / 文件中。**

Privacy Gateway 不只过滤原文，也过滤摘要。摘要也可能泄露姓名、交易金额、医疗信息、私信内容、关系网络、时间地点组合身份。

### 10.2 处理管线

```
Unicode normalize
→ Presidio Analyzer
→ 自定义中文 PII recognizers
→ spaCy / Stanza NER
→ Qwen3 8B 二分类复核
→ placeholder replacement
→ local SQLite mapping
→ JSON Schema 输出
```

### 10.3 自定义 PII Recognizer

基于 Microsoft Presidio（开源 PII 检测、脱敏、匿名化框架，支持 regex、NLP、pattern recognizer、自定义 pipeline）构建。

自定义 recognizers：

```
CN_PHONE
CN_ID_CARD
BANK_CARD_LUHN
EMAIL
ADDRESS_HINT
TOKEN
SESSION_ID
COOKIE
JWT
API_KEY
PRIVATE_KEY
OAuth token
```

### 10.4 Unicode 预处理

必须先做：

```python
unicodedata.normalize("NFKC", text)
remove_zero_width(text)
decode_url_encoding(text)
try_base64_decode_suspicious_segments(text)
```

### 10.5 NER

Primary：

```
spaCy zh / en
```

Secondary：

```
Stanza
HuggingFace token classification model
```

### 10.6 本地模型

#### Primary：Qwen3 8B via Ollama

```bash
ollama pull qwen3:8b
```

职责：

```
只回答：
"这段文本是否仍包含 PII / secret / private data？是 / 否 / 不确定"
```

禁止：

- 开放式摘要
- 安全策略解释
- 执行网页指令
- 根据网页内容改变规则

#### Optional：Qwen3 14B / 30B-A3B via MLX

用途：

- 已脱敏内容摘要
- 本地复杂分类
- 长文压缩

Qwen3 系列包含 8B、14B、30B-A3B 等规模。M1 Max 64GB 可运行 8B/14B，30B-A3B 可作为高级增强。Apple Silicon 上 MLX / vllm-mlx 类方案在本地推理吞吐上有明显优势，可作为高级优化方向。

### 10.7 PII 检测绕过防护

必须处理以下绕过手段：

- Unicode 同形字符
- 零宽字符
- Base64
- URL encoding
- 分隔符插入
- 表格拆分
- JSON key/value 隐藏
- 代码变量名泄露

防护措施：

- Unicode NFKC normalize
- remove zero-width
- decode common encodings
- key + value 都扫
- Luhn 银行卡检测
- Presidio custom recognizers
- Qwen3 二分类只做复核
- canary token 测试

### 10.8 摘要泄露防护

摘要也会泄露敏感信息（姓名、交易金额、医疗信息、私信内容、关系网络、时间地点组合身份），因此 Privacy Gateway 不只过滤原文，也过滤摘要。

### 10.9 Canary Token

给私域页面或测试数据加入假 token：

```
AI_CANARY_DO_NOT_LEAK_2026_xxxxx
```

如果出现在以下任何位置，立即阻断：

- Claude Code transcript
- MCP audit
- browser logs
- output markdown

---

## 11. 本地 RAG / 私域信息层

### 11.1 Primary：SQLite + FTS5 + sqlite-vec

个人开发者、单机、Local First、易备份、易审计、无常驻服务。sqlite-vec 是 SQLite vector search extension，运行范围广、依赖少，适合本地嵌入式检索。

架构：

```
documents.sqlite
  documents
  chunks
  embeddings
  pii_map
  access_log
  audit_log
```

### 11.2 Embedding

Primary：

```
BAAI/bge-m3
```

Secondary：

```
multilingual-e5-large
```

### 11.3 Reranker

Optional：

```
BAAI/bge-reranker-v2-m3
```

### 11.4 Qdrant 升级条件

当满足以下任一条件时引入 Qdrant：

```
> 200k chunks
> 多项目并发
> 需要 filter + payload indexing
```

---

## 12. 数据流

### 12.1 公开搜索流

```
Claude Code Research Mode
→ MCP Guard
→ SearXNG search
→ Top 20 results
→ URL normalize / dedupe / score
→ Top 5 Crawl4AI md
→ Input Sanitizer
→ Privacy Gateway light mode
→ redacted markdown + citations
→ Claude Code
```

### 12.2 JS-heavy 页面流

```
Claude Code Research Mode
→ Playwright MCP
→ AI-Public Profile
→ accessibility snapshot
→ selected interaction
→ extracted text
→ Input Sanitizer
→ Privacy Gateway
→ Claude Code
```

### 12.3 私域访问流

```
Human manually logs in once
→ AI-Private Chrome Profile

Claude Code Private Mode
→ MCP Guard
→ Chrome DevTools MCP
→ read-only snapshot / page text
→ Input Sanitizer
→ Privacy Gateway full mode
→ placeholder redacted JSON
→ Claude Code
```

### 12.4 写操作流

```
Agent proposes action
→ classify action risk

If action in:
- post
- comment
- like
- DM
- buy
- pay
- delete
- edit profile
- send email
- submit form

Then:
→ pause
→ show diff / target / account / page / payload
→ human approve
→ execute once
→ audit log
```

---

## 13. 安全设计

### 13.1 网页 Prompt Injection 防护

**攻击路径：** Agent 打开恶意网页 → 页面隐藏文本指令 → 诱导模型调用 evaluate_js → `document.cookie` / `localStorage` → 工具输出进入 Claude Code → 泄露到日志或回答。

**缓解措施：**

- 禁止 `document.cookie`、`localStorage`、`sessionStorage` 字符串出现在 JS 参数。
- `evaluate_js / execute_js` 默认禁用。
- 私域工具只暴露 read snapshot，不暴露 arbitrary JS。
- 输出层扫描 cookie/token 格式。
- Chrome DevTools MCP 只在 Private Mode 加载。

### 13.2 MCP Rug Pull 防护

**攻击路径：** 第 1 天安装安全 MCP server → 第 7 天 npm 包更新 → tool description 改成恶意 → Claude Code 重启加载新 schema → 模型被诱导调用高危工具。

**缓解措施：**

- 禁止 `@latest`。
- 禁止长期 `npx -y package`。
- 使用本地路径。
- lock commit hash。
- `mcp-scan whitelist TYPE NAME HASH`。
- tool schema diff。
- 新 tool / changed tool 必须人工确认。

### 13.3 恶意 MCP Server 文件读取防护

**攻击路径：** 恶意 MCP server → tool description 诱导模型调用 filesystem → 读取 `~/.ssh` / env / tokens → 通过搜索工具或浏览器外带。

**缓解措施：**

- Research Mode 不加载 filesystem / shell。
- Coding Mode 不加载浏览器 / 搜索。
- MCP server 容器只读 FS。
- 环境变量最小化。
- 不把 API key 传给不需要的 server。
- pf / container egress 限制。

### 13.4 Chrome Remote Debugging 防护

**攻击路径：** Chrome 9222 开着 → 恶意本机进程连接 CDP → 控制 AI-Private Profile → 读取页面 / 导航 / 执行 JS。

**缓解措施：**

- remote debugging 只绑定 localhost。
- 使用非默认 user-data-dir。
- Profile 不保存密码 / 支付信息。
- 任务结束关闭 Chrome。
- 不在 AI-Private Profile 打开网银 / 主邮箱。
- 高敏站点只人工浏览，不给 Agent。

### 13.5 搜索结果污染防护

**攻击路径：** 攻击者做 SEO → SearXNG 返回恶意页面 → Crawl4AI 提取 markdown → markdown 内含"忽略之前指令" → 模型照做。

**缓解措施：**

- external content 标记为 untrusted data。
- Input Sanitizer 移除指令型段落。
- Spotlighting / quote wrapping。
- 不允许网页内容触发工具调用。
- fetch 后先摘要为 facts，不保留指令语气。
- provenance 强制保留 source URL。

### 13.6 Privacy Gateway 绕过防护

**攻击路径：** 手机号写成 `138-５５５５-１２３４`、身份证 base64、token 藏在 JSON key、姓名拆在表格列。

**缓解措施：**

- Unicode NFKC normalize。
- remove zero-width。
- decode common encodings。
- key + value 都扫。
- Luhn 银行卡检测。
- Presidio custom recognizers。
- Qwen3 二分类只做复核。
- canary token 测试。

### 13.7 Session 过期封号防护

**攻击路径：** 登录态过期 → Agent 看到 login page → 反复尝试登录 / OTP / CAPTCHA → 平台风控 → 账号锁定。

**缓解措施：**

- snapshot 检测 `登录 / Sign in / CAPTCHA / 验证码 / 2FA`。
- 命中立即停止。
- macOS notification。
- 不自动输入密码。
- 不自动处理验证码。
- 手工重新登录。

---

## 14. 运维设计

### 14.1 日志

SQLite audit log 记录：

```
tool_calls
mcp_schema_hashes
browser_sessions
privacy_detections
policy_denials
canary_hits
errors
```

### 14.2 监控

本地 health check：

```bash
curl http://127.0.0.1:8080/search?q=test&format=json
curl http://127.0.0.1:11235/health
ollama ps
pgrep "Google Chrome"
```

### 14.3 自动恢复

```
SearXNG container       → restart unless-stopped
Crawl4AI container       → restart unless-stopped
Ollama                   → launchd
Privacy Gateway          → launchd
Chrome private           → 不自动恢复写任务
```

### 14.4 备份

**备份：**

```
.mcp.json
MCP lockfile
Privacy Gateway config
SQLite RAG DB
audit DB
SearXNG settings.yml
```

**不自动备份：**

```
Chrome cookies
session tokens
password store
payment autofill
```

### 14.5 完整运维清单

- SQLite audit log
- health check
- launchd 自动恢复
- Docker restart policy
- config backup
- profile backup 策略
- secret rotation
- MCP schema diff
- 每周安全扫描
- 每月恢复演练

---

## 15. 风险清单

| 等级 | 风险 | 缓解 |
|---|---|---|
| P0 | MCP tool poisoning / rug pull | mcp-scan、hash pin、schema diff、禁用 latest |
| P0 | 外部网页 prompt injection 触发 shell | mode 隔离，Research Mode 无任意 shell |
| P0 | Chrome remote debugging 泄露 Profile | 专用 Profile、localhost、任务后关闭 |
| P0 | Cookie / token 泄露 | 禁止 storage/cookie API、输出扫描 |
| P1 | 私域摘要泄露 | 先脱敏后摘要、JSON Schema |
| P1 | Session 过期封号 | 登录页 / CAPTCHA 检测，立即暂停 |
| P1 | 搜索污染 | domain scoring、Top-K fetch、provenance |
| P2 | SearXNG 上游限流 | engine health、fallback |
| P2 | Crawl4AI JS 渲染失败 | Playwright fallback |
| P2 | 本地模型误判 PII | Presidio + deterministic first |
| P3 | 容器 / 服务崩溃 | restart policy + health check |
| P3 | audit DB 损坏 | 定期备份 |

---

## 16. 实施路线图

### 16.1 Phase 1：最小可用安全搜索系统

**目标：** 在**现有 FORGE Factory** 上实现公开搜索 + 抓取 + 脱敏 + 审计（作为增量模块）。

1. 在现有项目中创建 `_infra/network/` 骨架（复用根结构）。
2. 部署 SearXNG（复用或添加根 docker/searxng/）。
3. 启用 JSON format。
4. 部署 Crawl4AI（复用根 docker/）。
5. 配置 Crawl4AI MCP。
6. 安装 mcp-scan。
7. 所有 MCP server 固定本地路径。
8. 编写 Privacy Gateway v1（放在 _infra/network/privacy_gateway/）：
   - Unicode normalize
   - Regex
   - Presidio
   - placeholder
9. 建 SQLite audit log（复用 runtime/）。
10. 集成到现有 forge CLI / Claude Code Research Mode。
11. 验证：
    - 搜索
    - 抓取
    - 脱敏
    - 审计
    - prompt injection 测试

### 16.2 Phase 2：浏览器与私域访问

**目标：** 安全访问登录态页面。

1. 创建 AI-Public Profile。
2. 创建 AI-Private Profile。
3. 手工登录目标私域站。
4. 安装 Playwright MCP。
5. 安装 Chrome DevTools MCP，固定版本。
6. 添加 MCP Guard hook：
   - 禁止 cookie
   - 禁止 localStorage
   - 禁止 sessionStorage
   - 禁止 arbitrary JS
   - 高危动作人工确认
7. 增加 session expiry detector。
8. 增加 macOS notification。
9. 红队演练：
   - hidden prompt
   - fake token
   - login expiry
   - malicious page

### 16.3 Phase 3：长期增强

1. SQLite + sqlite-vec Local RAG。
2. bge-m3 embeddings。
3. reranker。
4. Canary token framework。
5. mcp-firewall / MCPProxy 评估。
6. 多 Agent 子任务：
   - Researcher
   - Browser Reader
   - Privacy Auditor
   - Implementer
7. 每周自动：
   - mcp-scan
   - tool schema diff
   - dependency audit
   - engine health check
8. 每月灾难恢复演练。

---

## 17. 架构决策记录（ADR）

### ADR-NET-001：选择 SearXNG 作为 Primary Search

**决策：** 使用 SearXNG Docker 自托管作为公开搜索主入口。

**原因：** 免费、开源、本地部署、无 token API、支持 JSON API、隐私优先、与 Claude Code / MCP 易集成。

**放弃：** Tavily 核心依赖（SaaS）；Perplexity（SaaS）；Google/Bing API（API key / 配额 / 计费）；OpenWebUI Search 作为核心（过重）。

### ADR-NET-002：Crawl4AI 替代 FireCrawl

**决策：** Crawl4AI 是核心抓取 / Markdown 提取层。

**原因：** Apache-2.0、本地、MCP 支持、LLM-ready Markdown、轻于 FireCrawl、适合个人开发者。

**放弃 FireCrawl 核心：** 服务栈过重、自托管维护成本高、云版不符合 Local First、私域访问不应走 FireCrawl。

### ADR-NET-003：不使用默认独立 MCP Router

**决策：** 删除通用 MCP Router，采用 Claude Code native MCP + MCP Guard。

**原因：** Router 本身也是攻击面；Claude Code 已支持 MCP scopes 和 `.mcp.json`；Claude Code hooks 可做 PreToolUse；安全目标是 policy / audit / pinning，不是"多一层转发"。

**保留能力：** mcp-scan、schema hash、tool policy、audit、optional firewall / proxy。

### ADR-NET-004：Chrome DevTools MCP 只用于私域和调试

**决策：** Chrome DevTools MCP 不作为公开网页抓取主力。

**原因：** 它可暴露并修改浏览器实例数据；remote debugging port 风险高；私域登录态访问确实需要它；公开网页更适合 Crawl4AI / Playwright。

### ADR-NET-005：Playwright MCP + restricted CLI

**决策：** Playwright MCP 是默认 browser automation；CLI 只通过 wrapper。

**原因：** MCP 适合交互式自动化；CLI 省 token 但需要 shell；不能为了 token 省略权限边界；wrapper 可限制命令集合。

### ADR-NET-006：Privacy Gateway 采用 Presidio + deterministic first

**决策：** Privacy Gateway 不依赖单一 LLM。

**原因：** LLM 可被 prompt injection 影响；PII 检测需要确定性规则；Presidio 是成熟开源框架；本地 Qwen 只做二分类复核。

**放弃：** 纯 Regex、让 Qwen 做安全网关、原文进主模型后再过滤、无 schema 的自由摘要。

### ADR-NET-007：Local RAG 使用 SQLite + sqlite-vec

**决策：** 个人环境默认 SQLite + sqlite-vec，而不是 Qdrant / Weaviate / Milvus。

**原因：** 单机、可备份、可审计、低维护、足够个人规模、与 Privacy Gateway / audit 共用 SQLite 生态。

**升级条件：** chunk 数超过 20 万、多项目并发、复杂 metadata filter、独立服务化需求时引入 Qdrant。

---

## 18. 未来演进路线

### 18.1 预计成为主流的方向

**MCP + 安全治理：** MCP 生态会继续增长，但裸 MCP 会被淘汰。未来主流为 signed tool schema、tool hash pinning、MCP admission control、runtime tool policy、MCP audit、gateway / firewall / sandbox。

**Accessibility Tree / Structured Browser Automation：** 基于 accessibility tree 的浏览器自动化比像素级 computer use 更稳定、更可解释。

**Local RAG + Embedded Vector DB：** 个人开发者倾向 SQLite + FTS + vector extension，而非一开始就上重型 vector DB。

**本地小模型做隐私/分类/审计：** 本地 8B～14B 模型会成为 PII 检测、intent 分类、policy explanation、summarization、local RAG answer 的默认选择。

### 18.2 可能被淘汰或降级的方向

| 技术 | 判断 |
|---|---|
| 裸 `npx @latest` MCP | 必然淘汰 |
| 单 Agent 同时拥有 shell + browser + private data | 必然淘汰 |
| 纯 Regex Privacy Filter | 不够 |
| Pixel-only Computer Use | 退为 fallback |
| Cloud browser agent 处理私域数据 | 与 Local First 冲突 |
| FireCrawl self-host 作为个人核心 | 过重，降级 |
| 泛 MCP Router 无安全能力 | 伪基础设施 |

### 18.3 建议提前布局的方向

```
- MCP schema signing
- mcp-scan / mcp-firewall / MCPProxy 类工具
- Chrome / Web 原生 agent interface
- browser origin isolation for agents
- SQLite local memory
- profile-level browser permission
- canary token / audit replay
- agent task provenance
```

---

## 19. 明确排除的组件与方案

以下组件和方案明确不进入核心架构：

```
- FireCrawl 作为核心提取层
- 通用 MCP Router 作为默认组件
- npx @latest 作为长期安装方式
- 日常 Chrome Profile 用于 Agent
- Cloud browser agent (Browserbase / Operator / ChatGPT Agent)
- Tavily / SaaS 搜索作为核心依赖
- 小模型承担全部安全判断
- shell + browser + private data 同 session
- OpenWebUI / Perplexica / Vane 作为核心搜索层
- FireCrawl 用于私域内容提取
- WebMCP 作为确定路线（当前未找到足够稳定生产依据）
```

---


