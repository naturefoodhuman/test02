<!--\n创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)\n创建时间：2026-06-20 13:40:00 CST\n-->

# PROJECT_STATE —— 工厂运行状态 (v1.2.6)

**更新日期**：2026-06-20 13:40 CST  
**当前版本**：v1.2.6（Model Stress Test Connectivity）

## 1. 核心资产概览
- **系统版本**: v1.2.6 (Stable Hybrid + Benchmark Ready)
- **显存状态**: 动态管理中 (M1 Max 64G)
- **网关状态**: Smart Proxy (FastAPI) + AppleScript 驱动

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
- [x] **沙箱 Benchmark 执行**: ✅ 已完成（4 方案全部成功运行）
- [x] **Smart Proxy 连通性**: OK (4000 端口)
- [x] **Benchmark 配置链路**: ✅ 已打通（v1.2.6 核心里程碑）
- [ ] **真实 LLM 调用**: 需本地模型服务 + langgraph 依赖

## 4. 最近一轮大攻坚 (2026-06-20)
- **成就 1**（核心）：彻底修复 benchmark 启动报错
  - 问题：`full-check` 方案引用未定义模型 `local-fast`
  - 解决：移除 `fast_classify` 节点（无对应实现）
  - 结果：5 个压测方案全部可正常加载
- **成就 2**：完成 26 个 Python 文件全量语法 + 导入链检查
- **成就 3**：首次使用 Deploy Key 成功 push 到 GitHub
- **治理**：同步更新 PROJECT_STATE + CHANGELOG + routing_plans.yaml

## 5. 待办事项 (Next)
- [x] **沙箱 Benchmark 执行**：已完成（venv + 依赖安装 + 4 方案成功运行）
- [ ] 在 Mac 本地执行真实压测（需启动 Smart Proxy + 模型服务）
- [ ] 收集真实耗时 + divergence_score 数据（当前沙箱因无模型服务返回 0.0）
- [ ] 准备 v1.2.7（添加 benchmark 结果表格 + 真机验证）