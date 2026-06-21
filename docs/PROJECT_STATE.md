<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-20 22:40:00 CST
-->

# PROJECT_STATE —— 工厂运行状态 (v1.3.0-dossier)

**更新日期**：2026-06-20 22:40 CST  
**当前版本**：v1.3.0-dossier（Project Dossier V2 交付）

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
