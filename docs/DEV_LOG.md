# DEV LOG —— 逐轮开发日志

## 第 28 轮 · 2026-06-13
### 核心架构重构 (v1.0.5 Agno + LlamaIndex)
1. **技术栈升级**：废弃手写架构，全面引入 Agno (Agent/Team/Memory) + LlamaIndex (RAG) + ChromaDB (Vector)
2. **隐私合规**：禁用 Agno 遥测 (`AGNO_TELEMETRY=false`)，模型请求全走本地 Ollama (127.0.0.1)
3. **修复项**：
   - `orchestrator.py`：修复 f-string 语法错误、移除废弃 Agent 参数、适配 Agno 2.6 Team API
   - `expert.yaml`：修复嵌套结构导致 ID 为空的问题，增加 model 别名映射
   - `cli.py`：修复 ModuleNotFoundError，增强 PYTHONPATH 解析逻辑

## 第 27 轮 · 2026-06-13
### 规范修复与知识库升级
1. **修复规范**：HANDOFF.md 重写（补全保姆级 SOP + 排障表 + 检查清单）
2. **R2 穷尽调研**：完成 Vibe-Trading、quant-mind、Hands-On-AI 调研与决策记录 (D-011)
3. **方案 A**：专家知识库大幅升级（新增 case_patterns.md, negation_cases.md 等）
4. **方案 B**：引入 SKILL.md 系统 + LayeredDecisionEngine 分层决策引擎

## 第 26 轮 · 2026-06-13
### FB-14 Peer-Review 基础架构
1. 核心架构：`_factory/patterns/peer-review/` 模块初始化
2. 新增 3 位评审专家定义
3. CLI 集成：`debt review` 命令
