<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-08 22:08:00
-->


# ADR-001 — Project Bootstrap Skeleton

## Status

Accepted

## Date

2026-07-08

## Context

AI Parenting Copilot 已完成架构、工程设计与任务 Backlog，但项目目录内尚无可开发工程骨架。`APC-T001` 要求创建推荐目录结构、基础配置文件、项目级维护文档与开发入口，同时不得实现业务功能或改变既有架构。

用户最新指令明确：

- 项目目录大小写统一为 `projects/AI-Parenting-Copilot/`。
- 工厂能力背景直接使用工厂根目录 `PROJECT_DOSSIER_V5.md`。
- 删除 Office 临时锁文件。
- 根级 `HANDOFF.md`、`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md` 仅作为项目级同类文档写法参考。

## Decision

创建最小项目骨架：

- 项目根：`README.md`、`Makefile`、`pyproject.toml`、`.env.example`、`.gitignore`。
- 项目文档：`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/HANDOFF.md`。
- ADR 目录：`docs/ADR/ADR-001-project-bootstrap.md`。
- 服务端包占位：`server/app/__init__.py`。
- 目录占位：`android/`、`firmware/esp32c6/`、`config/`、`deploy/`、`runtime/`。
- 骨架测试：`tests/test_project_structure.py`。

本 ADR 不新增架构决策，只记录 `APC-T001` 的工程初始化事实。

## Consequences

- 后续 Agent 可从项目级 `docs/HANDOFF.md` 接手，不会误用工厂根目录任务文档。
- `APC-T002` 可在已存在的 `server/app/` 包内实现 FastAPI 应用壳。
- 真实基础设施、数据库、同步、Auth、事件和业务逻辑仍由后续任务逐步实现。
- `runtime/` 被 gitignored，仅保留 `.gitkeep`。

## Validation

`APC-T001` 完成后应通过：

```bash
make docs-check
make lint
make typecheck
make test
```
