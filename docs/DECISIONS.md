## D-013 · 立即迁移 LangGraph 1.0（最终架构 v1.1.0 拍板）
- **时间**：2026-06-15
- **决策**：按 `4-Final Architecture Design.md` 立即从 Agno 迁移到 `langgraph>=1.0.10` + `langgraph-checkpoint-sqlite>=3.0.1`，不再通过抽象层推迟。
- **原因**：
  1. Agno 在 6 个月内经历多次 breaking changes，API 稳定性差，维护成本高
  2. LangGraph 1.0 提供 API 稳定性承诺，原生支持 HUB-SPOKE（`Send`）、SqliteSaver 检查点、HITL 中断点
  3. 最终架构将 LangGraph 列为 P0，消除根源风险优于局部修补
- **执行策略**：
  1. 双轨运行：新 LangGraph 实现与旧 Agno 实现并存，直到 LangGraph 稳定 2 周后删除旧代码
  2. 渐进迁移：先落地图结构 + 平台层，再逐个接入真实 LLM、DataPrivacyGate、MemoryStore
  3. 测试先行：新增 `test_peer_review_langgraph.py` 作为新架构安全网
- **状态**：核心图结构与平台层已落地，16 个新测试通过，CLI 已切换入口。

## D-012 · 架构重构为 Agno + LlamaIndex (第28轮定论，已被 D-013 替代)
- **时间**：2026-06-13
- **决策**：废弃手写代码，拥抱 `agno>=2.6` + `llama-index-core>=0.12` + `chromadb>=0.6`。
- **核心修复**：
  1. `orchestrator.py` v1.0.5：加入防御性导入、禁用遥测、增加模型别名解析表 (local/primary -> qwen3.6...)
  2. 解决 Agno Team 默认回退 OpenAI 问题，强制指定本地 Ollama 模型
  3. 修复 Python 3.11 下 f-string 反斜杠语法错误
- **状态**：作为过渡实现保留，待 LangGraph 验证稳定后删除。
