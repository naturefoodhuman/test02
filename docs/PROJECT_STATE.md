<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-25 00:00:00
-->

# PROJECT_STATE —— 当前状态 SSOT

**更新日期**：2026-06-25 00:00 CST
**当前版本**：v1.4.7-dossier + Claude Code Alias Compatibility
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
- **多源调度升级**：`NetworkWorkflow` 已接入 `MultiSourceSearchOrchestrator`，保持 SearchProvider 接口兼容，并提供 intent route、SearXNG tier fallback 与可选 API fallback。
- **搜索风控系统性加固**：`SearXNGProvider v24` 已实现 per-engine Circuit Breaker、engine tier pool、CAPTCHA/rate-limit/timeout/forbidden 分类与 `unresponsive_engines` 反馈更新。
- **Engine Matrix 硬化**：`docker/searxng/settings.yml` 已切换为 anti-risk-control hardened 白名单配置，禁用 Google/Brave/Startpage/DDG scraping 主路径，优先 Wikipedia/Mojeek/Bing/Qwant/GitHub/arXiv/StackOverflow/HackerNews 等稳定源。
- **API 兜底层**：新增 Brave Search API、Tavily、Serper.dev providers；仅当 `BRAVE_API_KEY` / `TAVILY_API_KEY` / `SERPER_API_KEY` 环境变量存在时自动加载，密钥不进入仓库。
- **大规模风控特征诊断 v2**：`scripts/diagnostics/test_engine_risk_control.py` 支持 CAPTCHA/WAF 指纹识别、HTML snapshot、Prometheus metrics、JSON report 与 SLO 指标。
- **维基百科 / TLS 特殊站点处理**：`Crawl4AIProvider` 保留 UA/Magic payload；新增 optional `CurlCffiProvider`，仅对 known TLS guarded public domains 且安装 `curl_cffi` 时启用，不替换 Crawl4AI。

### E3 / E4 Search + Extract
- SearXNG provider（适配 8090 端口）、Crawl4AI provider（适配 v0.9.x API）。
- 具备 `markdown_v2` 与 HTML 深度解析剥壳能力。

### E5 / E9 Privacy & RAG
- 7层隐私管线（Unicode -> Regex -> NER -> Qwen -> Replace -> Schema -> Canary）。
- SQLite RAGStore，支持超长文本分段与向量缓存一致性校验。

### Finalization / Local Secrets / Runtime UX
- 本地 `.env` 与 `_infra/.env` 会被自动加载，解决 Tavily/Serper 等 API key 每次重启终端需手动 export 的问题；真实 `.env` 文件保持 gitignored。
- `TrafilaturaProvider` 已增加 bounded timeout，网络不可达时快速降级到 snippet fallback，避免端到端搜索被单页提取卡住。
- 当前联网功能已完成 Search / Extract / Privacy / RAG / MCP Guard / Browser / Ops / Diagnostics 的文档与测试闭环，剩余为真机长期稳定性观察。


### Training / Onboarding Documentation
- `docs/工厂使用手册.md` 已升级为 Claude Code for VS Code 日常主工作流版：强调自然语言对话驱动，终端 CLI 作为验证/自动化辅助。
- `docs/全功能最小示例项目.md` 已重新设计为 `mini-gratitude-control-tower`，覆盖普通功能与高风险能力安全演示。
- `docs/工厂能力覆盖检查.md` 已重建矩阵，当前覆盖率 76/76 = 100%。
- 新增 `docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`，并升级 `scripts/governance_check.py` + `make docs-check`，推动文档治理自动化常态化。
- 文档治理 P1 已落地：changed-files R5 阻断、Backlog/DEV_LOG 同步阻断、代码变更必须更新 CHANGELOG、架构触发词提示 ADR、自动生成 `docs/DOCUMENT_INDEX.md`；决策记录见 ADR-008。
- 文档治理 P2 已落地：pre-commit / GitHub Actions / launchd 自动化、no-write strict 检查、自动生成 `docs/AGENT_HANDOFF_SUMMARY.md`。

### Claude Code for VS Code alias compatibility
- 已补充当前 Claude Code for VS Code UI 中 Opus 4.8 / Sonnet 4.6 / Haiku 4.5 相关 alias 到本地 MTPLX 主模型映射，避免 VS Code 插件因 `claude-opus-*` / `claude-sonnet-*` alias 未注册而报模型不存在。
- VS Code 推荐使用 `ANTHROPIC_BASE_URL=http://localhost:4000` 与 `ANTHROPIC_API_KEY=sk-forge-local-anytoken`。
- `scripts/forge-start.sh` 已改为按端口清理 4000/4001，避免旧代理占用 4000 导致 `/v1/messages` 返回 Not Found。
- `_infra/smart_proxy.py` 已支持 Anthropic streaming SSE 转换，并默认限制本地模型输出 token，改善 VS Code Claude Code 面板长时间等待问题。
- 培训文档已修正 Claude Code for VS Code 操作方式：命令面板命令不在终端执行，首句优先用 `@HANDOFF.md` 等上下文附加，避免本地模型长工具链卡顿。

---

## 4. 最新测试基线

**运行命令**：`python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q`
**结果**：`358 passed, 3 skipped, 44 warnings`
**说明**：2 skipped 为沙盒缺少 Presidio 环境；warnings 均为 datetime.utcnow 弃用警告，不影响业务。全量单元与安全测试全部绿色通过。

---

## 5. 已知重大挑战

1. **上游元搜索引擎对 VPN/代理的无差别拦截**：SearXNG 通用默认引擎（Brave、DuckDuckGo、Startpage、Google）在节点代理 IP 下频繁触发 CAPTCHA。已通过 Engine Matrix 白名单、per-engine Circuit Breaker、tier fallback 与可选 API fallback 降低重复触发；根因仍需住宅代理或 API 搜索服务解决。
2. **上游 API 结构漂移**：Crawl4AI 与 Ollama SDK 参数持续迭代，已通过层级递归清洗（`deep_clean_content`）与强约束类型校验保持调用链稳定。
