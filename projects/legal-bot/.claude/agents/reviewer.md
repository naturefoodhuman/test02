<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# Subagent：reviewer

- **阶段**：BUILD（每次 tool-use 后由 Hooks 触发，非 LLM 确定性执行）
- **职责**：测试通过/失败判定、lint 检查、TASK_GRAPH 验证、熔断控制。
- **说明**：核心逻辑由 `.claude/hooks/` 脚本确定性执行，不依赖 LLM 主观判断（NFR-005）。
