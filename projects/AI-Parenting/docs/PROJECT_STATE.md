<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# PROJECT_STATE —— AI Parenting Copilot 当前状态 SSOT

> 本文件是项目级当前状态唯一事实来源，独立于工厂根 `PROJECT_STATE.md`。
> 与 `docs/TASK_BACKLOG.md` 状态保持一致；任何状态变更必须同步更新两处。

---

## 0. 当前里程碑

**Milestone 1 — P0-M0 工程地基**（APC-T001 ~ APC-T006）

---

## 1. 任务状态索引

| 任务 | 标题 | 状态 | 备注 |
|---|---|---|---|
| APC-T001 | 初始化项目目录与工程元数据 | ✅ DONE | 骨架占位完成，`make lint` / `make docs-check` 通过 |
| APC-T002 | FastAPI 应用壳、Settings、DI、公共基础类型 | ⬜ TODO | 下一个 |
| APC-T003 | 本地基础设施 Docker Compose 与 Alembic | ⬜ TODO | 依赖 T002 |
| APC-T004 | 核心数据库 Schema 初版 | ⬜ TODO | 依赖 T003 |
| APC-T005 | 结构化日志 / Metrics / Tracing / 健康端点 | ⬜ TODO | 依赖 T002 |
| APC-T006 | 审计日志服务与 @audit 装饰器 | ⬜ TODO | 依赖 T004,T005 |
| APC-T007 ~ T059 | 后续里程碑 | ⬜ TODO | 见 TASK_BACKLOG |

状态图例：✅ DONE / 🔄 IN_PROGRESS / ⬜ TODO / ⛔ BLOCKED

---

## 2. 已完成能力

- 项目目录骨架（`server/app/` 全领域子模块、`android/`、`firmware/esp32c6/`、`config/`、`deploy/`、`tests/`、`runtime/`）。
- `pyproject.toml`（依赖 + ruff + mypy + pytest 配置，Python 3.11+）。
- `Makefile`（test/lint/typecheck/docs-check/governance-check/run-dev/infra-up/db-migrate 等）。
- `.env.example`（PARENTING_ 前缀，分层加载，无真实密钥）。
- `.gitignore`（runtime/、.env、密钥、媒体、缓存一律忽略；保留 .gitkeep 与 fixtures）。
- `README.md`（项目入口与快速开始）。
- `docs/HANDOFF.md`、`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/CHANGELOG.md`。
- `docs/ADR/ADR-001-project-bootstrap.md`。
- `server/` 全包占位 `__init__.py`（无业务代码，待 APC-T002 起填充）。
- `runtime/.gitkeep`（确保 runtime/ 入库但内容被忽略）。

---

## 3. 进行中

无。APC-T001 已完成，等待启动 APC-T002。

---

## 4. 下一步

按 MVP 路径（TASK_BACKLOG §4）推进：

1. **APC-T002** — 实现 FastAPI 应用壳、Settings、DI 与公共基础类型（`server/app/main.py`、`settings.py`、`di.py`、`common/*`、`gateway/exception_handlers.py`）。

---

## 5. 已知风险 / 待办

- `make docs-check` / `make governance-check` 当前为占位提示，待工厂治理脚本接入后替换为真实检查。
- `runtime/` 子目录（db/logs/media/secrets）已存在但被 gitignore；首次使用时由应用按需创建。
- 占位 `__init__.py` 为空，ruff/mypy 对空包不报错，但 `make typecheck` 在有真实代码前意义有限。
