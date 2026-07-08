<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-09 01:15:00
-->


# PROJECT_STATE —— AI Parenting Copilot 当前状态 SSOT

**更新日期**：2026-07-08 CST
**当前阶段**：P0-M0 工程地基
**当前任务状态**：`APC-T001 DONE`、`APC-T002 DONE`、`APC-T003 BLOCKED`、`APC-T004 BLOCKED`、`APC-T005 DONE`、`APC-T006 BLOCKED`、`APC-T007 BLOCKED`、`APC-T008 BLOCKED`、`APC-T024 DONE`、`APC-T025 DONE`
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


### APC-T024 — 实现 Model Gateway Smart Proxy 客户端与 Routing Plan

状态：DONE

已完成：

- `server/app/model_gateway/client.py`：Smart Proxy `/v1/messages` 客户端，支持 chat 与 vision 请求、timeout、错误映射和 FakeModelClient。
- `server/app/model_gateway/routing.py`：项目级 routing plan loader。
- `config/routing_plans.yaml`、`config/models.yaml`：项目级模型路由与别名配置，实际运行仍由工厂 Smart Proxy / 根配置承载。
- 测试覆盖 routing 解析、Anthropic-compatible payload、vision payload、FakeModelClient。

### APC-T025 — 实现 Privacy Gateway 适配层与云出站安全测试

状态：DONE

已完成：

- `server/app/privacy/adapter.py`：通过适配层复用工厂 `_infra.network.privacy_gateway`，不复制实现。
- 云端文本出站前可调用 `PrivacyAdapter.prepare_cloud_text()` 进行 PII 脱敏与 canary 检查。
- 原始 image/video/audio/media 云出站通过 `reject_cloud_media()` 阻断。
- 测试覆盖邮箱/手机号脱敏、canary 阻断、原始媒体出站阻断。


---

## 3. 当前阻塞

### APC-T003 — 本地基础设施 Docker Compose 与 Alembic 初始化

状态：BLOCKED

已完成代码/配置：

- `deploy/docker-compose.yml`：PostgreSQL 15、Mosquitto 2、PowerSync official service。
- `deploy/.env.example`、Mosquitto config、PowerSync service/sync config、Postgres init SQL。
- `server/app/db.py`：SQLAlchemy async engine/session primitives 与 declarative Base。
- `alembic.ini`、`server/migrations/env.py`、`server/migrations/versions/.gitkeep`。
- `Makefile`：`infra-up`、`infra-down`、`infra-logs`、`db-migrate`、`db-current`。

阻塞原因：当前执行沙盒没有 Docker CLI，无法验证 `make infra-up` 后 PG/MQTT/PowerSync 容器健康，因此按 DoD 不能标记 DONE。


### APC-T004 — 创建核心数据库 Schema 初版

状态：BLOCKED

已完成代码/静态验证：

- `server/app/models.py`：SQLAlchemy metadata 初版，覆盖 family/user/device/baby/observation_event、领域派生表、derived_baby_state、alert、alert_delivery、sleep_session、family_knowledge、evidence_policy、sensor_event、camera_event、media_asset、audit_log、sync_state 等核心表。
- `server/migrations/versions/0001_initial_schema.py`：初版 Alembic migration，包含 updated_at trigger、audit_log append-only trigger 与 app_user revoke 保护。
- `python3 -m alembic -c alembic.ini upgrade head --sql` offline SQL 生成通过。

阻塞原因：当前执行沙盒没有 PostgreSQL/Docker，无法执行空库 `alembic upgrade head` 与迁移升降级集成验收，因此按 DoD 不能标记 DONE。

### APC-T006 — 实现审计日志服务与 `@audit` 装饰器

状态：BLOCKED

已完成代码/单元验证：

- `server/app/observability/audit.py`：AuditRecord、AuditActor、AuditService、MemoryAuditSink、AuditWriteError。
- `server/app/common/audit_decorator.py`：`@audit` 装饰器；高风险 mutating 操作无 AuditSink 时阻断。
- 测试覆盖 decorator before/after 捕获、高风险无审计 sink 阻断。

阻塞原因：当前执行沙盒没有 PostgreSQL/Docker，无法完成 audit_log 实际插入与 UPDATE/DELETE 被 DB 拒绝的集成验收，因此按 DoD 不能标记 DONE。


### APC-T007 — 实现 Auth/RBAC Domain、Repository 与 JWT 服务

状态：BLOCKED

已完成代码/单元验证：

- `server/app/auth/domain/models.py`：Role、DeviceKind、Family、User、Device、Principal。
- `server/app/auth/service/passwords.py`：PBKDF2-HMAC-SHA256 密码/PIN hash，明文不存储。
- `server/app/auth/service/jwt_service.py`：本地 HS256 JWT 签发/解析，claims 包含 user_id、family_id、role、device_id。
- `server/app/auth/service/auth_service.py`：family/admin 创建、登录、Principal 解析、RBAC allow/deny、设备注册用例。
- `server/app/auth/infra/repository.py`：AuthRepository protocol 与 InMemoryAuthRepository。
- 测试覆盖密码校验、JWT claims、RBAC allow/deny、设备注册。

阻塞原因：T004/T006 仍待 PostgreSQL 集成验收；DB-backed repository 与真实 audit_log 接入尚未完成，因此按 DoD 不能标记 DONE。

### APC-T008 — 实现 Auth API、设备注册与 seed_family 脚本

状态：BLOCKED

已完成代码/测试：

- `server/app/auth/api/routes.py`：`/api/v1/auth/init-family`、`/login`、`/refresh`、`/me`、`/devices/register`。
- `server/scripts/seed_family.py`：可运行的 dev/in-memory seed 脚本。
- `server/app/main.py`：dev/in-memory AuthService 注入与 auth router 注册。
- 测试覆盖 init-family → login → bearer token → me → device registration。

阻塞原因：当前实现为 dev/in-memory 模式；真实 family/user/device DB 持久化、seed DB 写入与 mutating audit_log 集成验收待 PostgreSQL，因此按 DoD 不能标记 DONE。

---

## 4. 当前未实现

- PostgreSQL / Mosquitto / PowerSync / Alembic 代码配置已接入，但容器运行验收尚未完成，归属 `APC-T003 BLOCKED`。
- 核心 Schema、审计、Auth/API 代码已完成但集成验收 BLOCKED；Event Store、Android 等均未开始。

---

## 5. 最新验证基线

在 `projects/AI-Parenting-Copilot/` 下运行：

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 40 source files
make test
# 36 passed, 1 warning
python3 -m uvicorn server.app.main:app --host 127.0.0.1 --port 8765
# /healthz smoke: HTTP 200
```

仓库根目录额外治理检查：`make docs-check` → `Blockers: 0; Warnings: 1`。该 warning 为架构敏感词提示，本轮未改变架构边界。

---

## 6. 下一步

最高优先级任务：

- Task ID：`APC-T003` / `APC-T004` / `APC-T006` / `APC-T007` / `APC-T008`
- 任务名称：完成 Docker/PostgreSQL 相关集成验收与 DB-backed Auth 持久化
- 状态：BLOCKED，等待具备 Docker CLI 的环境执行 `make infra-up`、`make db-migrate`、迁移升降级、audit_log immutability、Auth DB repository / seed DB 写入验证。

可并行候选：继续实现不依赖真实 DB 的事件契约、Rule Engine 纯逻辑或测试 fake，但不得把依赖 PostgreSQL 集成验收的任务标记 DONE。
