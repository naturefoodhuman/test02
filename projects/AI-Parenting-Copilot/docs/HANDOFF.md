<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-08 22:08:00
-->


# HANDOFF —— AI Parenting Copilot Agent 接手入口

> 本文件是 AI Parenting Copilot 项目级接手入口。任何新 Agent 必须先建立项目边界：本项目只处理 `projects/AI-Parenting-Copilot/` 内的育儿系统，不把工厂根目录 FEOS / Network / TASK_BACKLOG 当作本项目任务来源。

---

## 0. 必读顺序

1. `docs/HANDOFF.md`（本文件）
2. `docs/PROJECT_STATE.md`（当前状态 SSOT）
3. `docs/TASK_BACKLOG.md`（任务状态与验收标准）
4. `docs/ARCHITECTURE_FINAL.md`（唯一架构基线）
5. `docs/ENGINEERING_DESIGN.md`（工程实现蓝图）
6. 工厂根目录 `../../../PROJECT_DOSSIER_V5.md`（工厂能力背景）
7. `docs/DEV_LOG.md` 最新一轮
8. `docs/CHANGELOG.md` 最新一轮
9. `docs/ADR/` 决策记录

不要使用项目内旧拷贝 `docs/PROJECT_DOSSIER_V5.md` 作为执行依据。

---

## 1. 项目定位

AI Parenting Copilot 是家庭私有化 AI 育儿副驾驶系统，目标是在家庭局域网内通过 Mac M1 Max 家庭服务端与 Android App，实现低摩擦记录、离线同步、派生状态、规则安全、告警必达与克制 AI Copilot。

项目根目录：

```text
projects/AI-Parenting-Copilot/
```

---

## 2. 当前真实状态

截至 2026-07-08：

- `APC-T001` 已完成：项目骨架、基础配置、项目级维护文档与 ADR 已创建。
- 服务端业务代码尚未实现；`server/app/__init__.py` 仅为包占位。
- Android / firmware / config / deploy / runtime 仅为目录占位。
- 下一最高优先级任务是 `APC-T002`。

---

## 3. 当前下一步

Task ID：`APC-T002`

任务名称：实现 FastAPI 应用壳、Settings、DI 与公共基础类型

执行前必须再次确认：

- 不改变架构边界。
- 不引入新基础设施。
- FastAPI 应用壳只实现 `APC-T002` 范围，不提前实现 Auth/Event/DB worker。
- Settings 使用 `pydantic-settings`，支持 `PARENTING_` 前缀与 `__` 嵌套。
- 全局错误格式为 `{code,message,evidence,trace_id}`。

---

## 4. 常用命令

在项目根目录运行：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
```

`APC-T001` 阶段尚未实现 FastAPI，`make run-dev` 只输出提示。`APC-T002` 完成后再接入实际启动命令。

---

## 5. 文档 SSOT

- 当前状态：`docs/PROJECT_STATE.md`
- 任务状态：`docs/TASK_BACKLOG.md`
- 架构基线：`docs/ARCHITECTURE_FINAL.md`
- 工程设计：`docs/ENGINEERING_DESIGN.md`
- 开发流水：`docs/DEV_LOG.md`
- 变更记录：`docs/CHANGELOG.md`
- 工厂能力背景：工厂根目录 `../../../PROJECT_DOSSIER_V5.md`

冲突优先级：用户当前最新指令 → 本项目 `docs/HANDOFF.md` → `docs/ARCHITECTURE_FINAL.md` → `docs/ENGINEERING_DESIGN.md` → `docs/TASK_BACKLOG.md` → 工厂根目录 `PROJECT_DOSSIER_V5.md` → 源码历史实现。

---

## 6. 架构保护速查

禁止未经用户明确批准：

- 修改架构决策、技术路线、系统边界、模块职责、调用链、核心设计原则。
- 引入新的基础设施或框架。
- 替换已有核心组件。
- 擅自大规模重构。

必须遵守：

1. LLM 只走 Model Gateway。
2. 云端出站只走 Privacy Gateway。
3. 剂量 / 阈值 / 医疗判断只由 Rule Engine 产出。
4. 告警只走 Notification Orchestrator。
5. 所有 mutating 操作必须审计。
6. Android 离线记录不得丢失。

---

## 7. LLM 文件头规则

LLM 新建或修改 Markdown、Python、YAML、Shell 等文件时，必须在文件头记录：

```text
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：YYYY-MM-DD HH:MM:SS
```

JSON 文件不能写注释时，使用 `_forge_trace` 字段。
