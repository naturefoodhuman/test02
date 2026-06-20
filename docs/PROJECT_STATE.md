<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-21 17:00:00 CST
-->

# PROJECT_STATE —— 工厂运行状态 (v1.2.5)

## 1. 核心资产概览
- **系统版本**: v1.2.5 (Stable Hybrid)
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
- [x] **Smart Proxy 连通性**: OK (4000 端口)
- [x] **Protocol Translation**: OK (Anthropic 互通)
- [x] **VRAM LRU Unloading**: OK (防 OOM)
- [x] **Benchmark 链路**: OK (非 0.0s 真实输出)

## 4. 最近一轮大攻坚 (2026-06-20/21)
- **成就 1**: 彻底解决了 Claude Code 接入本地模型的协议障碍。
- **成就 2**: 实现了真机显存的动态扩缩容，彻底杜绝 M1 Max 死机问题。
- **成就 3**: 统一了 `models.yaml` 路由，所有本地流量归口 4000 端口。
- **治理**: 建立了 `_obsolete/` 目录，清理了 20+ 个陈旧文件。

## 5. 待办事项 (Next)
- [ ] 收集 Benchmark 正式压测表格，淘汰低效专家。
- [ ] 完善多项目断点续接 (forge resume) 的 UI 提示。
