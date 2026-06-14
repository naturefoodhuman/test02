## D-012 · 架构重构为 Agno + LlamaIndex (第28轮定论)
- **时间**：2026-06-13
- **决策**：废弃手写代码，拥抱 `agno>=2.6` + `llama-index-core>=0.12` + `chromadb>=0.6`。
- **核心修复**：
  1. `orchestrator.py` v1.0.5：加入防御性导入、禁用遥测、增加模型别名解析表 (local/primary -> qwen3.6...)
  2. 解决 Agno Team 默认回退 OpenAI 问题，强制指定本地 Ollama 模型
  3. 修复 Python 3.11 下 f-string 反斜杠语法错误
- **状态**：真机验证通过（冒烟测试 + 全流程测试成功）。
