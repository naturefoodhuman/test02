<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-08 22:55:00
-->


# PROJECT_STATE —— AI Parenting Copilot 当前状态 SSOT

**更新日期**：2026-07-08 CST
**当前阶段**：P0-M0 工程地基
**当前任务状态**：`APC-T001 DONE`、`APC-T002 DONE`、`APC-T005 DONE`；下一顺序任务 `APC-T003 TODO`
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

### APC-T002 — 实现 FastAPI 应用壳、Settings、DI 与公共基础类型

状态：DONE

已完成：

- `server/app/main.py` 提供 `create_app()` 与 `app`，支持 `python3 -m uvicorn server.app.main:app` 启动。
- `server/app/settings.py` 使用 `pydantic-settings`，支持 `PARENTING_` 前缀与 `__` 嵌套配置。
- `server/app/di.py` 提供 AppContainer 与 WorkerRegistry，预留 FastAPI lifespan worker 注册接口。
- `server/app/common/` 提供 ULID、timezone-aware clock、错误模型、Repository Protocol、内存事件总线占位。
- `server/app/gateway/exception_handlers.py` 固化全局错误格式 `{code,message,evidence,trace_id}`。
- `/healthz` 与 `/openapi.json` 可在未配置 DB 时以 dev/mock 模式访问。

### APC-T005 — 接入结构化日志、Metrics、Tracing 与基础健康端点

状态：DONE

已完成：

- `server/app/observability/logger.py`：structlog JSON 日志与 PII/raw_input/media path mask。
- `server/app/observability/metrics.py`：Prometheus 指标注册与 `/metrics` 输出。
- `server/app/observability/tracing.py`：OpenTelemetry 本地安全降级配置。
- `server/app/gateway/middleware/logging.py`：请求 request_id/trace_id 注入、结构化 HTTP 日志与 metrics 记录。
- `server/app/health/api.py`：基础健康端点与系统健康端点。

---

## 3. 当前未实现

- PostgreSQL / Mosquitto / PowerSync / Alembic 尚未接入，归属 `APC-T003`。
- 核心 Schema、审计、Auth、Event Store、Android 等均未开始。

---

## 4. 最新验证基线

在 `projects/AI-Parenting-Copilot/` 下运行：

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 20 source files
make test
# 11 passed, 1 warning
python3 -m uvicorn server.app.main:app --host 127.0.0.1 --port 8765
# /healthz smoke: HTTP 200
```

仓库根目录额外治理检查：`make docs-check` → `Blockers: 0; Warnings: 1`。该 warning 为架构敏感词提示，本轮未改变架构边界。

---

## 5. 下一步

最高优先级任务：

- Task ID：`APC-T003`
- 任务名称：本地基础设施 Docker Compose 与 Alembic 初始化
- 所属 Epic：E01 项目地基与运行治理
- 所属 Capability：C02 本地基础设施与数据库迁移

备注：当前沙盒无 Docker CLI，`APC-T003` 的容器健康验收需在具备 Docker 的 Mac 环境完成；未验证前不得标记 DONE。
