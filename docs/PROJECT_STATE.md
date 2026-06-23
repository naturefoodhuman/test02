<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-06-23 11:02:00
-->

# PROJECT_STATE —— 工厂运行状态 (v1.3.0-dossier)

**更新日期**：2026-06-23 11:02 CST
**当前版本**：v1.3.0-dossier + Network Increment（M4 MCP Guard 核心抽象完成）

## 1. 核心资产概览
- **系统版本**: v1.3.0-dossier (Project Dossier V2 + Streaming Smart Proxy + Real Model Call)
- **显存状态**: 动态管理中 (M1 Max 64G)
- **网关状态**: Smart Proxy v5.0 (SSE Streaming) + AppleScript 驱动

## 2. 模型分工状态 (A-File SSOT)
| 模型 ID | 角色 | 端口 | 显存 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| `mtplx-qwen36-27b` | 主大脑 | 8080 | 20G | 动态拉起 |
| `mtplx-gemma4` | 独立评审 | 8082 | 16G | 动态拉起 |
| `qwopus-35b` | 深度评审 | 8084 | 36G | 动态拉起 |
| `local-deepseek-r1` | 逻辑推理 | 11434 | 20G | 动态拉起 |
| `deepseek-pro` | 外部增强 | API | 0G | 随时可用 |

## 3. 运行健康检查
- [x] **配置交叉验证**: OK（load_all_configs 通过）
- [x] **全量方案加载**: OK（full-check / default / high-quality / all-local / mtplx-hybrid 全部健康）
- [x] **Smart Proxy 流式改造**: ✅ 已完成（SSE 直通 + 心跳 + 字段白名单）
- [x] **真实 LLM 调用**: ✅ **首次成功**（1132.5s 获得真实共识报告）
- [x] **自动模型拉起**: ✅ 已实现（ensure_server + AppleScript）
- [x] **Project Dossier V2**: ✅ 已交付（docs/dossier_v2/）

## 4. 最近一轮大攻坚 (2026-06-20 - Dossier)
- **成就 1**（架构治理）：完成 Project Dossier V2 全量交付
  - 输出：`docs/dossier_v2/PROJECT_DOSSIER_V2.md` + asset_manifest.json + evidence_index.csv + risk_register.csv + adr_candidates.md + diagram_sources.md
  - 识别：20 项风险/技术债，7 个 ADR 候选，18 个 P0/P1/P2 资产，50 条证据索引
  - 结论：Proxy 单点 / VRAM 竞态 / 无 CI / 测试 <15% 为 Top 风险
  - 接管计划：30/60/90 Day Handover Plan 已制订
- **成就 2**（里程碑延续）：首次获得真实 LLM 共识报告（前一轮）
  - 耗时：1132.5 秒（≈19 分钟）
  - 模型：Qwen3.6-27B-MTPLX + Gemma4-MTPLX
  - 结果：完整债务案件策略报告（分歧度 0.0）
- **成就 3**：实现生产级流式 Smart Proxy
  - SSE 原样透传
  - chunk 级超时（最终 600s）
  - 心跳保活（45s~60s）
  - 字段白名单解决 400 Bad Request


## 4.1 Network Privacy Gateway 阶段进展（2026-06-22）

- **E5-C1** InputSanitizer 完成（HTML 剥离 + Prompt Injection 检测 + 隐藏内容）
- **E5-C2** Unicode 规范化完成（NFKC + 零宽字符 + PII 检测专用 normalize）
- **E5-C3-S1-T1** PIIDetector ABC + PIIType / PIIEntity 完成，并已修复导入隔离：ABC 与基础模型不再因 `detectors/__init__.py` 提前加载 `PresidioDetector` 而依赖 `presidio_analyzer`
- **E5-C3-S1-T2** PresidioDetector 源码已存在；相关单测在未安装 `presidio_analyzer` 的最小沙箱中依赖门控跳过
- **E5-C3-S1-T3** 中文 PII recognizers 源码已存在；相关单测同样依赖门控跳过
- **E5-C3-S1-T4** Token / API Key / JWT / Cookie / Session / OAuth / Private Key recognizers 完成；同时提供不依赖 Presidio 的 deterministic regex scanner
- **E5-C4-S1-T1** SpaCyNERDetector 完成；支持 zh/en 模型加载、依赖注入测试、PERSON/ORG/GPE/LOC/FAC → PIIEntity 映射，并提供 spaCy 模型下载脚本
- **E5-C5-S1-T1** QwenPIIClassifier 完成；使用 Ollama Python client lazy import，prompt 强制三选一（是/否/不确定），temperature=0.0，num_predict=10，10s 超时，失败降级为 uncertain 不阻断主流程
- **E5-C6-S1-T1** PIIReplacer 完成；支持 `PII_{TYPE}_{INDEX}` 占位符替换、相同值复用、mapping_id、queryable in-process mapping store
- **E5-C6-S1-T2** PII Map DB 完成；优先支持 SQLCipher driver，当前最小沙箱无 SQLCipher 时使用 sqlite3 + field-level AES-256-CBC authenticated BLOB fallback，错误密钥无法解密 original
- **E5-C7-S1-T1** JSON Schema 输出验证完成；默认 schema 限制 `text` / `mapping_id` / `entities`，禁止 raw PII `value` 出现在输出实体中，校验失败抛 `SchemaValidationFailedError`
- **E5-C8-S1-T1** CanaryTokenMonitor 完成；支持配置驱动 canary token、suffix/wildcard/regex 匹配、命中立即抛 `CanaryTokenDetectedError`，审计日志仅记录 masked token 与 metadata
- **E5-C9-S1-T1** PrivacyGateway 主管线完成；组装 L1 Unicode normalize、L2 Presidio/regex、L3 spaCy NER、L4 Qwen 复核、L5 placeholder、L6 JSON Schema、L7 Canary，提供 `PrivacyContext(mode=light/full)`
- **E5-C9-S1-T2** `build_privacy_gateway` 工厂函数完成；可从 `config/network.yaml` 一行装配 detectors / qwen / replacer / PII map store / validator / canary monitor
- **E11-C2-S1-T1** Prompt Injection 安全测试完成；新增恶意 HTML fixtures 与 security tests，覆盖隐藏指令、display:none、visibility:hidden、HTML comment、Unicode 全角混淆、URL encoding、tool-call trigger；InputSanitizer 同步加固 NFKC/URL decode 前置与 hidden block 整体移除
- **E11-C4-S1-T1** PII 绕过测试完成；新增 deterministic common PII recognizers，覆盖 Unicode 全角、零宽插入、Base64 编码、URL encoding、分隔符/表格拆分、JSON key/value、代码变量隐藏、email、CN phone、Luhn bank card
- **E11-C6-S1-T1** Canary Token 端到端测试完成；覆盖 search result / extracted markdown / browser page / privacy output，验证任一位置出现 canary 立即阻断，audit 只记录 masked token metadata
- **E2-C1-S1-T1** MCP Server 安装脚本完成；实现 pinned git clone + exact commit checkout + lockfile-based install + mcp-scan admission + `config/mcp_lockfile.yaml`，禁止 `@latest` / branch / HEAD
- **E2-C2-S1-T1** mcp-scan 集成完成；新增 scanner parser / CLI / 脚本，支持解析 findings/issues/vulnerabilities/violations/warnings/errors、lockfile local_path 扫描，任一 finding 或失败状态返回非 0
- **E2-C3-S1-T1** MCP Schema Hash 校验完成；实现 canonical JSON SHA256、lockfile tool schema pin、tools/list 提取、tool description mutation 检测、schema change 写入 `mcp_schema_changes` 并抛 `MCPSchemaChangedError`
- **E2-C4-S1-T1** MCP Guard 核心抽象完成；定义 `MCPToolCall` / `MCPToolResult` / `GuardDecision` / `PolicyDecision`，实现 `MCPGuard.check()`、schema verification 集成与所有决策审计（只记录 arg_keys，不记录 raw args）
- **测试**：`test_mcp_guard.py` 7 passed；network unit+security 全量 242 passed / 2 skipped / 11 warnings；`compileall` 通过
- **当前单任务**：E2-C4-S1-T1 MCP Guard 核心抽象已完成
- **下一任务候选**：E2-C4-S1-T2 模式权限策略（尚未实现）
- **文档同步**：TASK_BACKLOG / DEV_LOG / CHANGELOG / PROJECT_STATE / `_infra/network/README.md` 已按源码状态更新

**验证命令**：
```bash
python -m pytest _infra/network/tests/unit/test_mcp_guard.py -q
# 7 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 242 passed, 2 skipped, 11 warnings
python -m compileall -q _infra/network
# pass
```

## 5. 待办事项 (Next)
- [ ] **P0 – 测试护栏**：补 llm_client / smart_proxy / privacy_gate 单测，覆盖率 15% → 60% （ADR-C002）
- [ ] **P0 – 网关加固**：/healthz + 熔断 + 重试 + 鉴权 Token （ADR-C001）
- [ ] **P0 – 配置收敛**：消除 projects/*/config 重复拷贝，统一继承根 config/ （ADR-C003）
- [ ] 收集多方案真实压测数据（high-quality / all-local / mtplx-hybrid）
- [ ] CI 基建：GitHub Actions pytest + ruff + pip-audit + SBOM
- [ ] 可观测性：OpenTelemetry trace + 结构化日志 （ADR-C005）
- [ ] 容器化交付：Dockerfile + docker-compose （ADR-C004）
- [ ] 准备 v1.3.0 正式版（多项目并行 + 断点续接）

## 6. Dossier 交付物索引
- **卷宗正文**：`docs/dossier_v2/PROJECT_DOSSIER_V2.md`
- **资产清单**：`docs/dossier_v2/asset_manifest.json` (18 项)
- **证据索引**：`docs/dossier_v2/evidence_index.csv` (50 条)
- **风险登记册**：`docs/dossier_v2/risk_register.csv` (20 项)
- **ADR 候选**：`docs/dossier_v2/adr_candidates.md` (7 篇)
- **图表源**：`docs/dossier_v2/diagram_sources.md`

**接管必读顺序（更新）**：
1. `docs/dossier_v2/PROJECT_DOSSIER_V2.md` §1 Executive Takeover Brief
2. `HANDOFF.md`
3. `docs/dossier_v2/risk_register.csv`
4. `docs/PROJECT_STATE.md`（本文件）

## 7. Repository Cleanup State

- **最近清理时间**：2026-06-20
- **审计报告**：`docs/repository-audit.md`
- **清理报告**：`docs/repository-cleanup-report.md`
- **过期资产目录策略**：`/_obsolete/`  ignore，不 push 到 GitHub，保留在本地。
- **用户保留要求**：`projects/legal-bot/`、`projects/project-b/`、`retro-data-share/` 已复位并保持 active。
- **本轮仓库净化重点**：将一次性诊断/修复脚本、运行日志、历史设计/旧实现集中纳入 `_obsolete/`。
- **Dossier 交付物位置**：`docs/dossier_v2/` – 6 个文件，已纳入版本控制。
