<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-08 22:08:00
-->


# PROJECT_STATE —— AI Parenting Copilot 当前状态 SSOT

**更新日期**：2026-07-08 CST
**当前阶段**：P0-M0 工程地基
**当前任务状态**：`APC-T001 DONE`，下一任务 `APC-T002 TODO`
**状态说明**：本文件是 AI Parenting Copilot 项目级当前状态 SSOT；工厂根目录文档仅作为工厂能力与治理规则参考。

---

## 1. 项目定位

AI Parenting Copilot 是家庭私有化 AI 育儿副驾驶系统。项目源码与项目级文档位于：

```text
projects/AI-Parenting-Copilot/
```

项目必须严格遵守 `docs/ARCHITECTURE_FINAL.md` 与 `docs/ENGINEERING_DESIGN.md`，不得将工厂根目录 `TASK_BACKLOG`、Network 或 FEOS 文档当作本项目任务来源。

工厂能力背景读取工厂根目录：

```text
../../../PROJECT_DOSSIER_V5.md
```

项目内旧拷贝 `docs/PROJECT_DOSSIER_V5.md` 不作为执行 SSOT。

---

## 2. 当前已完成

### APC-T001 — 初始化项目目录与工程元数据

状态：DONE

已完成：

- 创建项目根 README / Makefile / pyproject / `.env.example` / `.gitignore`。
- 创建项目级维护文档：PROJECT_STATE、DEV_LOG、CHANGELOG、HANDOFF。
- 创建 ADR：`docs/ADR/ADR-001-project-bootstrap.md`。
- 创建服务端包占位：`server/app/__init__.py`。
- 创建 Android / firmware / config / deploy / runtime 目录占位。
- 删除用户指定的 Office 临时锁文件。
- 统一项目文档中的目录大小写为 `projects/AI-Parenting-Copilot/`。

---

## 3. 当前未实现

- FastAPI 应用壳尚未实现，归属 `APC-T002`。
- PostgreSQL / Mosquitto / PowerSync / Alembic 尚未接入，归属 `APC-T003`。
- 核心 Schema、审计、Auth、Event Store、Android 等均未开始。

---

## 4. 最新验证基线

在 `projects/AI-Parenting-Copilot/` 下运行：

```bash
make docs-check
make lint
make typecheck
make test
```

当前 `APC-T001` 骨架验证应全部通过；若本机未安装 `ruff` / `mypy`，Makefile 会明确提示跳过正式 ruff/mypy 检查。

---

## 5. 下一步

最高优先级任务：

- Task ID：`APC-T002`
- 任务名称：实现 FastAPI 应用壳、Settings、DI 与公共基础类型
- 所属 Epic：E01 项目地基与运行治理
- 所属 Capability：C01 项目骨架与配置
