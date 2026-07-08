<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-09 05:55:00
-->


# CHANGELOG —— AI Parenting Copilot 需求变更与文件影响

> 记录 AI Parenting Copilot 项目级需求变更、任务状态变更和文件影响。工厂根目录 `docs/CHANGELOG.md` 仅作格式参考，不作为本项目状态 SSOT。

## Latest Change Index

- **最新完成任务**：验收依赖修复、`APC-T031` Alert dev API、`APC-T032` Notification fake channels、`APC-T033` Notification fan-out 纯逻辑；均 BLOCKED 待 DB/设备集成验收。
- **当前状态**：项目骨架、API 壳、可观测性、模型网关、隐私适配、auth、events、rule engine、copilot/orchestrator、alert/notification dev 链路已推进；基础设施/schema/audit/DB 持久化待 Docker/PostgreSQL 验收。
- **下一任务**：继续告警升级状态机/Device Health/Scheduler 纯逻辑或等待集中验收反馈。











---

## [第 11 轮] 2026-07-09 — 验收依赖修复 + APC-T031 / APC-T032 / APC-T033 纯逻辑完成

### 需求变动

- 修复用户集中验收中出现的 `No module named alembic/structlog/ulid`、ruff/mypy/pytest-asyncio 未安装问题。
- 完成 Alert dev repo/API、Notification fake channels、Notification fan-out 纯逻辑。
- 由于真实 DB/audit/device 通道未验收，T031/T032/T033 标记 BLOCKED。

### 文件影响

新增/修改：

- `server/scripts/ensure_dev_deps.py`
- `Makefile`
- `pyproject.toml`
- `server/app/notification/*`
- `config/notification.yaml`
- notification/alert tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 87 source files
make test
# 72 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 10 轮] 2026-07-09 — APC-T030 P0 Copilot wrappers 纯逻辑完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB 的代码。
- 完成 Proactive、FamilyMemory、Vaccine、Growth、Medication Basic P0 Copilot wrappers。
- 由于前置 Rule/Orchestrator/Dose/Memory tasks 未 DONE 且真实 DB/audit 未验收，T030 标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/copilots/proactive_copilot.py`
- `server/app/copilots/family_memory.py`
- `server/app/copilots/vaccine_planner.py`
- `server/app/copilots/growth_milestone.py`
- `server/app/copilots/medication_safety.py`
- `server/app/orchestrator/orchestrator.py`
- `tests/test_p0_copilots.py`
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 80 source files
make test
# 67 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 9 轮] 2026-07-09 — APC-T026 / APC-T027 / APC-T028 / APC-T029 纯逻辑完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB 的代码。
- 完成 Memory snapshot、Copilot base/Logger、Orchestrator dev API 与 Dose Interceptor 安全逻辑。
- 由于前置 State Engine、Memory DB/RAG、真实 audit_log 与编排集成验收未完成，相关任务标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/memory/*`
- `server/app/copilots/*`
- `server/app/orchestrator/*`
- Orchestrator/Copilot/Dose tests
- `server/app/main.py`
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 75 source files
make test
# 62 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 8 轮] 2026-07-09 — APC-T022 / APC-T023 纯逻辑完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB 的代码。
- 完成 Vaccine Planner 与 Growth Rule Domain 的纯逻辑和 golden tests。
- 由于前置 Rule Engine DB/audit 验收、生产规则审查与完整 WHO 表未完成，T022/T023 标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/rule_engine/domains/vaccine.py`
- `server/app/rule_engine/domains/growth.py`
- `config/rules/vaccine/cn-nip-2024.yaml`
- `config/rules/growth/who-0-5.yaml`
- `tests/golden/rules/vaccine_cases.yaml`
- `tests/golden/rules/growth_cases.yaml`
- vaccine/growth tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 62 source files
make test
# 53 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 7 轮] 2026-07-09 — APC-T018 / APC-T020 / APC-T021 纯逻辑完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB 的代码。
- 完成 Rule Engine kernel、Medication rules、Triage/Threshold rules 的纯逻辑和 golden tests。
- DB-backed EvidencePolicy/audit、State Engine 输入与真实告警联动仍待后续验收，因此相关任务标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/rule_engine/*`
- `config/rules/README.md`
- `config/rules/medication/base.yaml`
- `config/rules/triage/base.yaml`
- `config/alert_thresholds.yaml`
- `tests/golden/rules/*`
- rule engine / medication / triage / threshold tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 60 source files
make test
# 49 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 6 轮] 2026-07-09 — APC-T009 / APC-T010 dev 代码完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB 的代码。
- 完成 ObservationEvent 契约、idempotency、in-memory EventRepository 与 dev Events API。
- 由于真实 DB repository、PowerSync 写入契约与 audit_log 持久化仍需 PostgreSQL，T009/T010 标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/events/domain/observation_event.py`
- `server/app/events/service/idempotency.py`
- `server/app/events/infra/repository.py`
- `server/app/events/api/routes.py`
- `server/app/main.py`
- Events domain/repository/API tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 49 source files
make test
# 42 passed, 1 warning
```

---

## [第 5 轮] 2026-07-09 — APC-T007 / APC-T008 dev 代码完成，集成验收 BLOCKED

### 需求变动

- 用户确认继续并行开发不依赖真实 DB 的代码。
- 完成 Auth/RBAC 纯逻辑、dev/in-memory repository、JWT、本地 Auth API 与 dev seed 脚本。
- 由于 DB repository、seed DB 写入与 mutating audit_log 仍需 PostgreSQL，`APC-T007`、`APC-T008` 标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/auth/domain/*`
- `server/app/auth/service/*`
- `server/app/auth/infra/repository.py`
- `server/app/auth/api/routes.py`
- `server/scripts/seed_family.py`
- `server/app/main.py`
- `server/app/settings.py`
- Auth service/API tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 40 source files
make test
# 36 passed, 1 warning
python3 server/scripts/seed_family.py
# dev/in-memory seed JSON output
```

---

## [第 4 轮] 2026-07-09 — APC-T004 / APC-T006 代码完成，集成验收 BLOCKED

### 需求变动

- 继续尽可能多推进任务。
- 完成核心 schema 与审计服务/装饰器代码；由于当前沙盒无 Docker/PostgreSQL，相关集成验收无法完成，按 DoD 标记 BLOCKED。

### 文件影响

新增/修改：

- `server/app/models.py`
- `server/migrations/versions/0001_initial_schema.py`
- `server/app/observability/audit.py`
- `server/app/common/audit_decorator.py`
- `tests/test_schema_models.py`
- `tests/test_audit_decorator.py`
- `Makefile`
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 29 source files
make test
# 30 passed, 1 warning
python3 -m alembic -c alembic.ini upgrade head --sql
# offline SQL generation passed
```

---

## [第 3 轮] 2026-07-08 — APC-T003 / APC-T024 / APC-T025

### 需求变动

- 继续尽可能多推进任务。
- `APC-T003` 已完成代码与配置，但当前沙盒无 Docker CLI，无法完成容器健康验收，状态设为 BLOCKED。
- 完成依赖已满足且不受 DB 阻塞的 `APC-T024` 与 `APC-T025`。

### 文件影响

新增/修改：

- `deploy/docker-compose.yml`、`deploy/.env.example`、`deploy/postgres/init/001-create-powersync-storage.sql`
- `deploy/mosquitto/mosquitto.conf`
- `deploy/powersync/service.yaml`、`deploy/powersync/sync-config.yaml`
- `alembic.ini`、`server/app/db.py`、`server/migrations/env.py`
- `server/app/model_gateway/*`
- `server/app/privacy/*`
- `config/routing_plans.yaml`、`config/models.yaml`
- `tests/test_infra_config.py`、`tests/test_db.py`、`tests/test_model_gateway.py`、`tests/test_privacy_adapter.py`
- `Makefile`、`pyproject.toml`、`.env.example`
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 26 source files
make test
# 25 passed, 1 warning
```

---

## [第 2 轮] 2026-07-08 — APC-T002 / APC-T005

### 需求变动

- 用户要求后续每轮尽可能多开发任务。
- 在完成最高优先级 `APC-T002` 后，继续完成依赖已满足的 `APC-T005`。
- `APC-T003` 需要 Docker 容器健康验收；当前沙盒无 Docker CLI，因此未标记 DONE。

### 文件影响

新增：

- `server/__init__.py`
- `server/app/main.py`
- `server/app/settings.py`
- `server/app/di.py`
- `server/app/common/*.py`
- `server/app/gateway/exception_handlers.py`
- `server/app/gateway/middleware/logging.py`
- `server/app/health/api.py`
- `server/app/observability/logger.py`
- `server/app/observability/metrics.py`
- `server/app/observability/tracing.py`
- `tests/test_settings_ids_errors.py`
- `tests/test_app_health_observability.py`

修改：

- `Makefile`：`run-dev` 接入 uvicorn，docs-check 增加 T002/T005 文件检查。
- `pyproject.toml`：加入 FastAPI、pydantic-settings、python-ulid、structlog、Prometheus、OpenTelemetry 等依赖。
- `.env.example`：加入 observability 配置。
- `docs/TASK_BACKLOG.md`：同步 `APC-T002`、`APC-T005` 状态为 DONE。
- `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/HANDOFF.md`：同步当前状态与下一任务。

### 验证

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

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 1 轮] 2026-07-08 — APC-T001 项目骨架初始化

### 需求变动

- 用户确认 SSH Deploy Key 已添加，批准开始开发并允许后续 Push。
- 用户要求统一目录大小写为仓库实际路径 `projects/AI-Parenting-Copilot/`。
- 用户要求工厂能力背景直接使用工厂根目录 `PROJECT_DOSSIER_V5.md`，不使用项目内旧拷贝。
- 用户要求删除 Office 临时锁文件 `docs/~$TASK_BACKLOG家庭私有化 AI 育儿副驾驶系统-gpt-5.5-high.docx`。
- 执行 `APC-T001`，创建项目骨架与项目级维护文档。

### 文件影响

新增：

- `README.md`
- `Makefile`
- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`
- `docs/HANDOFF.md`
- `docs/ADR/ADR-001-project-bootstrap.md`
- `server/app/__init__.py`
- `tests/test_project_structure.py`
- `android/.gitkeep`
- `firmware/esp32c6/.gitkeep`
- `config/.gitkeep`
- `deploy/.gitkeep`
- `runtime/.gitkeep`

修改：

- `docs/ARCHITECTURE_FINAL.md`：仅修正项目目录大小写与工厂根目录 Dossier 引用。
- `docs/ENGINEERING_DESIGN.md`：仅修正项目目录大小写与工厂根目录 Dossier 引用。
- `docs/TASK_BACKLOG.md`：同步 `APC-T001` 状态与工厂根目录 Dossier 引用。

删除：

- `docs/~$TASK_BACKLOG家庭私有化 AI 育儿副驾驶系统-gpt-5.5-high.docx`

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 1 source file
make test
# 3 passed

# 仓库根目录额外治理检查：
cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```
