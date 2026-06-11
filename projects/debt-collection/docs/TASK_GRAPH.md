<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 00:10:00 CST
-->

# TASK_GRAPH

> status ∈ {TODO, IN_PROGRESS, DONE, BLOCKED}。粒度：单任务可独立测试/回滚，约 50–300 行。
> ⚠️ 进入 BUILD 需先过 HITL Gate-2（老板确认架构）。

## Task: setup-project-skeleton
- status: TODO
- model-used: local/primary
- desc: 建 src/debt 骨架 + pyproject + .gitignore(数据目录) + 测试目录

## Task: models-and-sqlite
- status: TODO
- depends-on: setup-project-skeleton
- desc: 债务/证据/报告数据模型 + SQLite 存储(脱敏)

## Task: ledger-crud
- status: TODO
- depends-on: models-and-sqlite
- desc: F1 台账增删改查；支持 ≥8 笔(AC-1)

## Task: timeline-prescription
- status: TODO
- depends-on: models-and-sqlite
- desc: F3 诉讼时效计算与预警(AC-3)；纯逻辑+单测

## Task: compliance-checker
- status: TODO
- depends-on: setup-project-skeleton
- desc: F6 合规自检：扫描非法/施压内容(AC-4)；纯逻辑+单测

## Task: integrate-ingestion
- status: TODO
- depends-on: models-and-sqlite
- desc: F2 接工厂 ingestion，把资料结构化并关联债务

## Task: integrate-acquisition
- status: TODO
- depends-on: models-and-sqlite
- desc: F4 接工厂 acquisition，生成待查清单+归档(AC-4)

## Task: strategy-report
- status: TODO
- depends-on: ledger-crud, timeline-prescription, integrate-acquisition, compliance-checker
- desc: F5 策略报告生成(含执行可行性)；GLM+法条+忠实度校验(AC-2/AC-6)

## Task: cli-wireup
- status: TODO
- depends-on: ledger-crud, timeline-prescription, strategy-report
- desc: 串起 CLI 命令(录入/列表/时效/取数/报告)

## Task: model-ab-test
- status: TODO
- depends-on: strategy-report
- desc: 【工厂压测】local/primary vs cloud/glm 做策略推理质量对比，结论写 RETRO
