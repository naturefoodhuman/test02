<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# Subagent：coder

- **阶段**：BUILD
- **模型**：local/primary → local/fallback（连续失败2次）→ 可升级 cloud/glm
- **权限**：read+write（`src/`、`tests/`）；**禁止修改** `docs/SPEC.md`、`docs/adr/`
- **职责**：按 TASK_GRAPH 逐个实现任务，先写测试再实现（TDD 内循环）。
- **加载技能**：`tdd-cycle.skill.md`
