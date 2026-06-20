<!--\n创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)\n创建时间：2026-06-20 17:10:00 CST\n-->

# PROJECT_STATE —— 工厂运行状态 (v1.2.9)

**更新日期**：2026-06-20 17:10 CST  
**当前版本**：v1.2.9（Real LLM Call Success）

## 1. 核心资产概览
- **系统版本**: v1.2.9 (Streaming Smart Proxy + Real Model Call)
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

## 4. 最近一轮大攻坚 (2026-06-20)
- **成就 1**（里程碑）：首次获得真实 LLM 共识报告
  - 耗时：1132.5 秒（≈19 分钟）
  - 模型：Qwen3.6-27B-MTPLX + Gemma4-MTPLX
  - 结果：完整债务案件策略报告（分歧度 0.0）
- **成就 2**：实现生产级流式 Smart Proxy
  - SSE 原样透传
  - chunk 级超时（最终 600s）
  - 心跳保活（45s~60s）
  - 字段白名单解决 400 Bad Request
- **成就 3**：完成全套诊断与修复工具链
  - `scripts/diagnose_proxy.sh`
  - `scripts/test_streaming_plan.py`
  - `scripts/start_streaming_proxy.sh`

## 5. 待办事项 (Next)
- [ ] 收集多方案真实压测数据（high-quality / all-local / mtplx-hybrid）
- [ ] 优化 MTPLX 启动参数（--reasoning-effort low 等）
- [ ] 准备 v1.3.0（多项目并行 + 断点续接）


## 6. Repository Cleanup State

- **最近清理时间**：2026-06-20
- **审计报告**：`docs/repository-audit.md`
- **清理报告**：`docs/repository-cleanup-report.md`
- **过期资产目录策略**：`/_obsolete/` 为本地归档，已加入 `.gitignore`，不 push 到 GitHub。
- **用户保留要求**：`projects/legal-bot/`、`projects/project-b/`、`retro-data-share/` 已复位并保持在仓库中。
- **本轮仓库净化重点**：停止跟踪既有 `_obsolete/`，归档一次性诊断/修复脚本与运行日志到本地 `_obsolete/`，补齐审计/清理报告。
