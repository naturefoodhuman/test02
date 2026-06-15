<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# TASK_GRAPH

> 机器可读格式。每个 Task 完成必须更新 status（pre-commit Hook 会拦 IN_PROGRESS）。
> status ∈ {TODO, IN_PROGRESS, DONE, BLOCKED}

## Task: setup-project-structure
- status: TODO
- model-used: local/primary
- glm-cost: 0
- tests-passed: pending
- fallback-used: no

## Task: example-feature
- status: TODO
- depends-on: setup-project-structure
