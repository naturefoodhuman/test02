<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建/修改时间（北京时间，精确到秒）：2026-06-12 00:40:00 CST
-->

# TASK_GRAPH

> status ∈ {TODO, IN_PROGRESS, DONE, BLOCKED}。粒度：单任务可独立测试/回滚，约 50–300 行。
> 第16轮升级：加入情报库/知识/动态重算（ADR-006）。

## Task: setup-project-skeleton
- status: DONE
- model-used: local/primary
- desc: 建 src/debt 骨架 + pyproject + .gitignore(数据/runtime) + 测试目录

## Task: models-and-sqlite
- status: DONE
- depends-on: setup-project-skeleton
- desc: 债务/证据/情报/时间线/报告数据模型 + SQLite 存储(脱敏)

## Task: ledger-crud
- status: DONE
- depends-on: models-and-sqlite
- desc: F1 台账增删改查；支持 ≥8 笔(AC-1)

## Task: timeline-prescription
- status: DONE
- depends-on: models-and-sqlite
- desc: F3 诉讼时效计算与预警(AC-3)；纯逻辑+单测

## Task: compliance-checker
- status: DONE
- depends-on: setup-project-skeleton
- desc: F6 合规自检：扫描非法/施压/骚扰/威胁/捏造内容(AC-4)；纯逻辑+单测

## Task: intel-store
- status: DONE
- depends-on: models-and-sqlite
- desc: 情报库：录入/管理新情报(来源/可信度/策略影响)(ADR-006)

## Task: case-timeline
- status: DONE
- depends-on: intel-store, ledger-crud
- desc: 案件时间线：聚合债务关键日期+沟通+情报+取数为一条时间线

## Task: knowledge-legal
- status: DONE
- depends-on: setup-project-skeleton
- desc: knowledge：从法规库取法条+本地执行口径(防幻觉)；V1 先做接口+本地知识占位

## Task: integrate-ingestion
- status: DONE
- depends-on: models-and-sqlite
- desc: F2 接工厂 ingestion，把资料结构化并关联债务

## Task: integrate-acquisition
- status: DONE
- depends-on: models-and-sqlite
- desc: F4 接工厂 acquisition，生成待查清单+归档(AC-4)

## Task: strategy-dynamic
- status: DONE
- depends-on: ledger-crud, timeline-prescription, compliance-checker, intel-store
- desc: F5 策略生成+动态重算(新情报→增量更新)+合法筹码识别(AC-2/AC-6/ADR-006)

## Task: cli-wireup
- status: DONE
- depends-on: ledger-crud, timeline-prescription, intel-store, case-timeline
- desc: 串起 CLI(录入债务/加情报/看时效/看时间线/取数/出策略)

## Task: model-ab-test
- status: TODO
- depends-on: strategy-dynamic
- desc: 【工厂压测】local/primary vs cloud/glm 做策略推理质量对比，结论写 RETRO
