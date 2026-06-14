<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-13 23:50:00 CST
-->

# PROJECT STATE —— 当前进度快照

- Phase 1: 基础设施 ✅ (LiteLLM 网关 + 遥测已打通)
- Phase 2: 试点项目 (debt-collection) ✅ (已结项，Lesson 已沉淀)
- Phase 2.5: 专家系统 FB-11/12 ✅ (债务律师专家已上线，万级知识库已注入)
- Phase 2.6: Peer-Review 多专家评审 FB-14 ✅ (v1.0.5 Agno+LlamaIndex+ChromaDB 架构重构完成，真机验证通过)

## 核心资产状态
- **专家系统**：`debt-lawyer.expert` (本地 R1 驱动 + 981 段《办案手册》知识)
- **评审专家团**（3 位，已修复 ID 缺失）：
  - `risk-assessor.expert` (ID: risk-assessor, model: qwen3.6:35b-a3b-q8_0)
  - `compliance-auditor.expert` (ID: compliance-auditor, model: qwen3.6:35b-a3b-q8_0)
  - `execution-strategist.expert` (ID: execution-strategist, model: qwen3.6:35b-a3b-q8_0)
- **Peer-Review 引擎**：`_factory/patterns/peer-review/` (v1.0.5: Agent/Team/ChromaDB/RAG)
- **SKILL.md 技能系统**：`_factory/skills/` 下 3 个技能 + 1 模板
- **分层决策**：`LayeredDecisionEngine` 类（铁闸硬编码 → AI 参考 → AI 生成）
- **模型网关**：三级路由 (在线 → 本地 R1 → 离线模板)，别名映射表 (MODEL_ALIAS_MAP)
- **环境矩阵**：
    - 主环境: `.venv` (Python 3.11, agno/llama-index/chromadb 已安装)
    - MinerU 环境: `runtime/mineru_env` (Python 3.12)

## 待办事项 (Backlog)
- [ ] FB-13: 场景化 RAG (针对复杂案件的深度检索优化)
- [ ] model-ab-test: local/primary vs cloud/glm 策略推理质量对比
- [ ] 持久化记忆系统: 跨轮次案例积累 + FTS5 全文搜索
