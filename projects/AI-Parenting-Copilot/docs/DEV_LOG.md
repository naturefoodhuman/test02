<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-09 01:15:00
-->


# DEV LOG —— AI Parenting Copilot 逐轮开发日志

## Latest Development Index

- **当前状态 SSOT**：`docs/PROJECT_STATE.md`
- **任务状态 SSOT**：`docs/TASK_BACKLOG.md`
- **最新完成**：`APC-T007` Auth/RBAC 代码与 `APC-T008` Auth API/seed dev 代码；二者均因 DB/audit 集成验收 BLOCKED
- **当前测试基线**：`make docs-check && make lint && make typecheck && make test` → `36 passed, 1 warning`；seed_family dev 脚本可运行；根目录 `make docs-check` Blockers 0
- **建议下一步**：继续实现不依赖真实 DB 的事件契约或 Rule Engine 纯逻辑；等待 Docker/PostgreSQL 后统一解除 BLOCKED。





---

## 第 5 轮 · 2026-07-09（APC-T007 Auth/RBAC 代码 + APC-T008 Auth API dev 代码）

**目标**：按用户指示继续并行开发不依赖真实 DB 的代码，严格不将依赖 PostgreSQL 集成验收的任务标记 DONE。

**状态变更**：

- `APC-T007`：TODO → BLOCKED（domain/service/JWT/RBAC/in-memory repo/unit tests 完成；DB repo 与真实审计验收待 PostgreSQL）
- `APC-T008`：TODO → BLOCKED（dev/in-memory Auth API 与 seed 脚本完成；DB 持久化与 audit_log 集成验收待 PostgreSQL）

**完成内容**：

1. **APC-T007 Auth/RBAC**：
   - `server/app/auth/domain/models.py`：Role、DeviceKind、Family、User、Device、Principal。
   - `server/app/auth/service/passwords.py`：PBKDF2-HMAC-SHA256 hash/verify，明文不存储。
   - `server/app/auth/service/jwt_service.py`：本地 HS256 JWT，claims 包含 user_id/family_id/role/device_id。
   - `server/app/auth/service/auth_service.py`：family/admin 创建、登录、token Principal、RBAC、设备注册。
   - `server/app/auth/infra/repository.py`：AuthRepository Protocol 与 InMemoryAuthRepository。

2. **APC-T008 Auth API / seed dev**：
   - `server/app/auth/api/routes.py`：`/api/v1/auth/init-family`、`/login`、`/refresh`、`/me`、`/devices/register`。
   - `server/scripts/seed_family.py`：dev/in-memory seed 脚本，可在无 DB 环境运行。
   - `server/app/main.py`：注册 auth router，并在 dev/mock 模式注入 InMemoryAuthRepository AuthService。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 40 source files
make test
# 36 passed, 1 warning
python3 server/scripts/seed_family.py
# outputs in-memory family_id/admin_user_id/access_token JSON

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

当前实现已支持 dev/in-memory flow，但还未接入 PostgreSQL Auth repository、真实 seed DB 写入与 mutating audit_log 集成验收。因此 `APC-T007`、`APC-T008` 均保持 `BLOCKED`。

---

## 第 4 轮 · 2026-07-09（APC-T004 Schema 代码 + APC-T006 Audit 代码）

**目标**：继续推进 DB 相关任务的代码实现，但严格按 DoD 处理无法在当前沙盒完成的 PostgreSQL 集成验收。

**状态变更**：

- `APC-T004`：TODO → BLOCKED（metadata/migration/static/offline SQL 完成；等待 PostgreSQL 空库 upgrade/downgrade 验收）
- `APC-T006`：TODO → BLOCKED（service/decorator/unit tests 完成；等待 audit_log DB insert/update/delete 集成验收）

**完成内容**：

1. **APC-T004 Schema 初版**：
   - `server/app/models.py`：SQLAlchemy metadata，覆盖架构与工程设计要求的核心表。
   - `server/migrations/versions/0001_initial_schema.py`：Alembic 初版 migration。
   - migration 包含：updated_at trigger、audit_log append-only trigger、`REVOKE UPDATE, DELETE ON TABLE audit_log FROM app_user` 条件执行。
   - schema 测试覆盖 required tables、ObservationEvent PK/状态字段/索引、audit immutability SQL。
   - Alembic offline SQL：`python3 -m alembic -c alembic.ini upgrade head --sql` 通过。

2. **APC-T006 Audit 代码**：
   - `server/app/observability/audit.py`：AuditActor、AuditRecord、AuditService、MemoryAuditSink、AuditWriteError。
   - `server/app/common/audit_decorator.py`：`@audit` 装饰器。
   - 单元测试覆盖 before/after 捕获与高风险操作无审计 sink 时阻断。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
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

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

当前沙盒无 Docker/PostgreSQL，无法完成 `APC-T004` 的空库 `alembic upgrade head`、迁移升降级集成测试，也无法完成 `APC-T006` 的 audit_log DB 插入与 UPDATE/DELETE 被拒绝验证。因此二者均保持 `BLOCKED`，未标记 DONE。

---

## 第 3 轮 · 2026-07-08（APC-T003 基础设施代码 / APC-T024 Model Gateway / APC-T025 Privacy Adapter）

**目标**：继续尽可能多推进任务；严格遵守架构边界与 DoD。

**状态变更**：

- `APC-T003`：TODO → BLOCKED（代码/配置/静态验证完成；Docker 容器健康验收受环境阻塞）
- `APC-T024`：TODO → DONE
- `APC-T025`：TODO → DONE

**完成内容**：

1. **APC-T003 代码与配置**：
   - `deploy/docker-compose.yml`：PostgreSQL 15、Mosquitto 2、PowerSync official service。
   - PowerSync 使用 `journeyapps/powersync-service:latest`；为避免引入架构外 MongoDB，bucket storage 配置为 PostgreSQL。
   - `server/app/db.py`：SQLAlchemy async engine/session primitives。
   - `alembic.ini`、`server/migrations/env.py`：Alembic 初始化。
   - Makefile 增加 `infra-up`、`infra-down`、`infra-logs`、`db-migrate`、`db-current`。
   - 测试覆盖 compose/service.yaml 配置、Postgres URL normalize、Alembic offline SQL generation。

2. **APC-T024 Model Gateway**：
   - 新增 `server/app/model_gateway/`。
   - 支持 Smart Proxy `/v1/messages`、chat、vision、routing plan、FakeModelClient。
   - 新增 `config/routing_plans.yaml` 与 `config/models.yaml`。
   - 测试使用 httpx MockTransport，CI 不调用真实模型。

3. **APC-T025 Privacy Adapter**：
   - 新增 `server/app/privacy/adapter.py`，通过适配层复用工厂 `_infra.network.privacy_gateway`。
   - 文本云出站前执行 PII 脱敏与 canary 检查。
   - 原始媒体云出站显式阻断。
   - 测试覆盖 PII 脱敏、canary 阻断、媒体出站阻断。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 26 source files
make test
# 25 passed, 1 warning

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

当前沙盒无 Docker CLI，无法执行 `make infra-up` 容器健康验收，因此 `APC-T003` 不满足完整 DoD，状态保持 `BLOCKED`，没有标记 DONE。

---

## 第 2 轮 · 2026-07-08（APC-T002 FastAPI 应用壳 + APC-T005 可观测性基础）

**目标**：在不改变架构边界的前提下，完成 `APC-T002`；由于 `APC-T005` 仅依赖 `APC-T002`，同步完成可观测性基础。`APC-T003` 需要 Docker 容器健康验收，当前沙盒无 Docker CLI，因此未标记 DONE。

**状态变更**：

- `APC-T002`：TODO → IN_PROGRESS → DONE
- `APC-T005`：TODO → IN_PROGRESS → DONE
- `APC-T003`：保持 TODO，作为下一顺序任务

**完成内容**：

1. **FastAPI 应用壳（APC-T002）**：
   - `server/app/main.py`：`create_app()`、全局 `app`、lifespan、health router、metrics endpoint。
   - `server/app/settings.py`：`pydantic-settings`，支持 `PARENTING_` 与 `__` 嵌套。
   - `server/app/di.py`：AppContainer、WorkerRegistry，预留 worker 生命周期接口。
   - `server/app/common/`：ULID、timezone-aware clock、AppError/ErrorResponse、Repository Protocol、InMemoryEventBus。
   - `server/app/gateway/exception_handlers.py`：统一错误格式 `{code,message,evidence,trace_id}`。

2. **可观测性基础（APC-T005）**：
   - `server/app/observability/logger.py`：structlog JSON 日志、敏感字段与 PII mask。
   - `server/app/observability/metrics.py`：Prometheus metrics registry 与 `/metrics`。
   - `server/app/observability/tracing.py`：OpenTelemetry SDK provider，未配置 exporter 时安全降级。
   - `server/app/gateway/middleware/logging.py`：request_id/trace_id 注入、结构化请求日志、HTTP 指标记录。
   - `server/app/health/api.py`：`/healthz` 与 `/api/v1/system/health`。

3. **测试补充**：
   - `tests/test_settings_ids_errors.py`：settings env override、ULID、timezone-aware clock、异常映射。
   - `tests/test_app_health_observability.py`：health/openapi、metrics、请求日志 request_id、PII mask。

**架构影响**：

- 无架构变更。
- 无新增基础设施。
- 未实现业务 worker、Auth、Event Store、DB 连接或同步逻辑。
- LLM / Rule Engine / Privacy Gateway / Notification Orchestrator 边界未改变。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
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

**风险 / 备注**：

- `APC-T003` 需要 Docker；当前沙盒 `docker` 命令不存在，因此后续若实现 T003，容器健康验收需要用户 Mac 或可用 Docker 环境配合。
- FastAPI TestClient 在当前依赖组合下输出 `StarletteDeprecationWarning`，不影响测试结果。

---

## 第 1 轮 · 2026-07-08（APC-T001 项目骨架初始化）

**目标**：严格依据 `docs/TASK_BACKLOG.md` 执行首个任务 `APC-T001`，只创建项目骨架和维护文档，不实现业务功能。

**状态变更**：

- `APC-T001`：TODO → IN_PROGRESS → DONE
- `APC-T002`：保持 TODO，作为下一最高优先级任务

**完成内容**：

1. 创建项目根工程元数据：
   - `README.md`
   - `Makefile`
   - `pyproject.toml`
   - `.env.example`
   - `.gitignore`

2. 创建项目级维护文档：
   - `docs/PROJECT_STATE.md`
   - `docs/DEV_LOG.md`
   - `docs/CHANGELOG.md`
   - `docs/HANDOFF.md`
   - `docs/ADR/ADR-001-project-bootstrap.md`

3. 创建项目骨架目录：
   - `server/app/__init__.py`
   - `android/.gitkeep`
   - `firmware/esp32c6/.gitkeep`
   - `config/.gitkeep`
   - `deploy/.gitkeep`
   - `runtime/.gitkeep`
   - `tests/test_project_structure.py`

4. 按用户最新指令完成清理与文档一致性修正：
   - 删除 `docs/~$TASK_BACKLOG家庭私有化 AI 育儿副驾驶系统-gpt-5.5-high.docx`。
   - 将项目文档内目录名统一为 `projects/AI-Parenting-Copilot/`。
   - 明确工厂能力背景使用工厂根目录 `PROJECT_DOSSIER_V5.md`，项目内旧拷贝不作为执行 SSOT。

**架构影响**：

- 无架构变更。
- 无技术路线变更。
- 无模块职责变更。
- 无新增基础设施。
- 本轮仅落地 `APC-T001` 要求的工程骨架。

**验证**：

```bash
make docs-check
make lint
make typecheck
make test
```

**风险 / 备注**：

- `APC-T001` 阶段尚未实现 FastAPI，因此 `make run-dev` 仅输出明确提示。
- 如果本地未安装 `ruff` / `mypy`，Makefile 会提示跳过正式 ruff/mypy 检查；后续任务引入开发依赖后应执行完整静态检查。
