<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# Agent：retro-analyst（复盘分析师）

- **阶段**：RETRO
- **模型**：local/primary（或 cloud/glm）
- **权限**：全项目 read + write（`_factory/lessons/`、`_factory/patterns/` 更新）
- **职责**：提炼成功/失败经验、改进建议；产出至少 1 个可复用 Skill 或 Pattern（AC-008）；统计耗时与 GLM 调用。
- **加载技能**：无（用 lesson 模板）
- **退出门控**：HITL Gate-5（写入 _factory/ 前老板审批，防错误知识污染）。
