<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-13 16:55:00 CST
-->

# PROJECT STATE —— 当前进度快照

- Phase 1: 基础设施 ✅ (LiteLLM 网关 + 遥测已打通)
- Phase 2: 试点项目 (debt-collection) ✅ (已结项，Lesson 已沉淀)
- Phase 2.5: 专家系统 FB-11/12 🟢 RUNNING (债务律师专家已上线，万级知识库已注入)

## 核心资产状态
- **专家系统**：`debt-lawyer.expert` (本地 R1 驱动 + 981 段《办案手册》知识)
- **模型网关**：三级路由 (在线 -> 本地 R1 -> 离线模板) 已在策略模块跑通。
- **环境矩阵**：
    - 主环境: 项目根目录 `.venv` (Python 3.11)
    - MinerU 环境: `runtime/mineru_env` (Python 3.12)

## 待办事项 (Backlog)
- [ ] FB-13: 场景化 RAG (针对复杂案件的深度检索优化)
- [ ] FB-14: 专家 Peer-Review 模式 (多 Agent 博弈)
