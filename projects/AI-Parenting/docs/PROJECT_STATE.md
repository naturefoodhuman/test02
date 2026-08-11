<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# PROJECT_STATE —— AI Parenting Copilot 当前状态 SSOT

> 本文件是项目级当前状态唯一事实来源，独立于工厂根 `PROJECT_STATE.md`。
> 与 `docs/TASK_BACKLOG.md` 状态保持一致；任何状态变更必须同步更新两处。

---

## 0. 当前里程碑

**Milestone 2 — P0-M1 事件溯源与同步**（APC-T007 ~ APC-T012，进行中）

> Milestone 1（APC-T001 ~ APC-T006）已完成；当前进入 Epic E02 事件层。

---

## 1. 任务状态索引

| 任务 | 标题 | 状态 | 备注 |
|---|---|---|---|
| APC-T001 | 初始化项目目录与工程元数据 | ✅ DONE | 骨架占位完成，`make lint` / `make docs-check` 通过 |
| APC-T002 | FastAPI 应用壳、Settings、DI、公共基础类型 | ✅ DONE | 应用壳可启动，/healthz 200，ruff/mypy 干净，39 测试通过 |
| APC-T003 | 本地基础设施 Docker Compose 与 Alembic | ✅ DONE | compose 三服务就位，alembic 框架可加载，51 测试通过 |
| APC-T004 | 核心数据库 Schema 初版 | ✅ DONE | 28 表 ORM + 初始迁移已应用，91 测试通过 |
| APC-T005 | 结构化日志 / Metrics / Tracing / 健康端点 | ✅ DONE | structlog JSON + PII mask、Prometheus /metrics、OTel no-op tracing、/readyz 增强探活；ruff/mypy 干净，104 测试通过 |
| APC-T006 | 审计日志服务与 @audit 装饰器 | ✅ DONE | AuditService append-only + @audit 装饰器 + 0002/0003 迁移（timestamptz + append trigger）；ruff/mypy 干净，118 测试通过 |
| APC-T007 | Auth/RBAC Domain、Repository 与 JWT 服务 | ✅ DONE | Role(Admin/Caregiver/Viewer/System)+Principal+TokenClaims+权限表、PBKDF2 密码哈希、HS256 JWT（标准库）、AuthService(登录/RBAC/建家建人)、SqlAlchemyUserRepository；ruff/mypy 干净，160 测试通过 |
| APC-T008 | Auth API、设备注册与 seed_family 脚本 | ✅ DONE | /api/v1/auth login/refresh/register-device/me + get_principal_dep 鉴权依赖 + DeviceRepository + seed_family.py；ruff/mypy 干净，169 测试通过 |
| APC-T009 | ObservationEvent Domain、Repository 与幂等写入 | ✅ DONE | ObservationEvent Pydantic 契约 + Source/SyncStatus/ProcessingStatus 枚举 + SqlAlchemyObservationEventRepository（event_id 幂等 upsert）+ EventService(record/correct/soft_delete)；ruff/mypy 干净，207 测试通过 |
| APC-T010 | Events API：创建、查询、纠错、软删除 | ✅ DONE | /api/v1/events POST/GET/{id}/correct/DELETE + RBAC(event:write/read) + EventContext(EventService+AuditService 共享 session) + @audit 留痕；ruff/mypy 干净，217 测试通过 |
| APC-T011 | PG LISTEN/NOTIFY 事件总线与事件变更触发器 | ✅ DONE | 0004 迁移(observation_event AFTER INSERT/UPDATE/DELETE → pg_notify events.changed) + PgListenEventBus(asyncpg add_listener) + EventWorker(订阅+recover_pending 崩溃恢复) + EventsSettings.pg_listen_enabled；ruff/mypy 干净，230 测试通过 |
| APC-T012 ~ T059 | 后续里程碑 | ⬜ TODO | 见 TASK_BACKLOG |

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
- **APC-T002**：FastAPI 应用壳与公共基础类型：
  - `server/app/settings.py`（pydantic-settings，`PARENTING_` 前缀 + `__` 嵌套，分层加载，dev/prod 多环境）。
  - `server/app/common/ids.py`（ULID 生成，26 字符 Crockford base32，时间有序）。
  - `server/app/common/clock.py`（timezone-aware UTC 时钟，Protocol + SystemClock，测试可注入替身）。
  - `server/app/common/errors.py`（领域异常层次 `ParentingError` + 子类，对齐 ENGINEERING_DESIGN §9.1；+ `ErrorEnvelope{code,message,evidence,trace_id}`）。
  - `server/app/common/repository.py`（`Repository[T]` Protocol，runtime_checkable）。
  - `server/app/common/event_bus.py`（PG LISTEN/NOTIFY 协议 + InMemoryEventBus 占位，dev/mock 用）。
  - `server/app/di.py`（进程级 `Container` + FastAPI Depends 工厂，惰性单例，测试可替换）。
  - `server/app/gateway/exception_handlers.py`（领域异常 → HTTP + 统一错误信封，含 422/404/500 兜底）。
  - `server/app/main.py`（FastAPI 应用工厂 `create_app` + `/healthz` + `/readyz` + worker 注册接口预留 + lifespan）。
  - 测试：`server/tests/unit/common/*`（ids/clock/errors/repository/event_bus/di/settings）+ `server/tests/integration/test_healthz.py`，37 passed。
- **APC-T003**：本地基础设施与 Alembic 初始化：
  - `deploy/docker-compose.yml`（PostgreSQL 15-alpine + Eclipse Mosquitto 2 + PowerSync Service，healthcheck，卷持久化，§14 Bootstrap 顺序）。
  - `deploy/mosquitto/mosquitto.conf`（本地 dev：监听 1883、允许匿名、持久化）。
  - `config/powersync/config.yaml` + `sync-rules.yaml`（占位；sync rules 待 APC-T004 Schema 定型后填充，架构 §9.2）。
  - `server/app/db.py`（SQLAlchemy async engine + async_sessionmaker，URL/pool 来自 Settings.database，pool_pre_ping，惰性单例，reset/dispose）。
  - `server/migrations/env.py`（Alembic async env，URL 从 Settings 注入不硬编码，target_metadata 占位待 T004）。
  - `alembic.ini`（script_location=server/migrations，日志配置）。
  - `Makefile` 增补：`infra-logs`/`infra-reset`/`db-current`/`db-history`/`db-revision`。
  - 测试：`server/tests/unit/common/test_db.py`（engine/session factory 惰性/单例/reset/dispose/pool_pre_ping）+ `test_alembic_config.py`（alembic.ini 解析、env.py 语法、versions 目录、compose 服务声明、mosquitto/powersync 配置存在），51 passed。
  - 独立库 `AI_parenting_dev`（裁决 2026-08-10，与兄弟项目 `parenting` 库隔离）；`deploy/compose-env.example` + `parenting-env.example`（`.env.example` 因 harness 拦截以等价样例提供）。
- **APC-T004**：核心数据库 Schema 初版（28 表 ORM + 初始迁移）：
  - `server/app/models/`（base/core/events/logs/derived/rules，按域分文件，共享 `Base`）。
  - 28 张表：family/user/device/baby/observation_event + 13 个 *_log（feeding/diaper/sleep/temperature/supplement/vaccine/medication/symptom/jaundice/milestone/growth/solid_food/media_asset）+ derived_baby_state/alert/alert_delivery/sleep_session/sensor_event/camera_event + family_knowledge/evidence_policy/audit_log/sync_state。
  - 通用 mixin：`ULIDPrimaryKey`（String(26)）、`TimestampMixin`（created_at/updated_at timezone-aware）、`SoftDeleteMixin`（is_deleted + partial index）。
  - 约束：device.kind/baby.sex/alert.level/alert.status/sleep_session.state/observation_event.source+sync_status+processing_status 枚举 CHECK；evidence_policy(type,region,version) UNIQUE；family_knowledge(family_id,key) UNIQUE；observation_event idx(baby_id,event_type,start_time DESC)。
  - `server/migrations/versions/9dc5086c5ca6_initial_schema.py`（autogenerate + 手补）：全表 `updated_at` trigger（`parenting_set_updated_at()` 函数 + 26 表 trigger）；`audit_log` REVOKE UPDATE/DELETE（append-only，§22.2）。
  - `server/migrations/env.py` `target_metadata = Base.metadata`；`server/migrations/script.py.mako`（alembic 官方 async 模板）。
  - 测试：`test_models.py`（表/列/约束/索引/软删除/timestamp 元数据校验，20+ 用例）+ `test_migration_apply.py`（integration：28 表/26 trigger/audit_log append-only/alembic 版本，4 用例），91 passed。
- **APC-T005**：结构化日志 / Metrics / Tracing / 健康端点：
  - `server/app/observability/logger.py`（structlog JSON → stdout；`bind_context`/`get_context`/`clear_context` contextvars；`mask_pii` 递归脱敏：敏感 key 整体 `***` + 手机号/邮箱/身份证正则 + 媒体路径文件名脱敏）。
  - `server/app/observability/metrics.py`（prometheus_client：parenting_record_latency_seconds / voice_normalization_success_ratio / sync_lag_seconds / offline_backfill_* / alert_delivery_total / rule_engine_evaluations_total / llm_calls_total / device_online 等 §10.2 指标占位）。
  - `server/app/observability/tracing.py`（OpenTelemetry no-op tracer，未配 exporter 时安全降级；`current_trace_id` 与 logger trace_id 贯穿）。
  - `server/app/health/api.py`（`/readyz`：DB ping `SELECT 1` + EventBus 状态；`/metrics`：Prometheus exposition；`/healthz` 仍在 main.py 进程存活）。
  - `server/app/gateway/middleware/logging.py`（每请求生成 request_id ULID + 入站 X-Trace-Id 透传/生成，bind_context 注入 contextvars，响应回写 X-Trace-Id/X-Request-Id，记录 method/path/status/duration_ms，PII 经 mask_pii）。
  - `server/app/main.py` 增补：`_configure_logging` + `add_request_logging` + `register_health_routes` 装配。
  - 测试：`server/tests/unit/common/test_pii_mask.py`（敏感 key/正则/媒体路径/递归/bind_context 脱敏/clear_context，7 用例）+ `server/tests/integration/test_observability.py`（request_id header / trace_id 透传与生成 / /metrics Prometheus 格式 / /readyz 200，6 用例），104 passed。
  - 修复：`bind_context` 原先对 kwargs 值逐个跑 mask_pii（字符串不知 key 名，敏感 key 的整体脱敏失效）→ 改为 `mask_pii(dict(kwargs))` 走 dict 分支，命中 `_SENSITIVE_KEYS` 整体替换。
  - 修复：`tests/conftest.py` `client` fixture 增加 `reset_db()`，避免 `test_migration_apply`（asyncio.run 独立循环）遗留的进程级 engine 绑定到已关闭循环，导致后续 `/readyz` check_db 拿死连接 → 503。
- **APC-T006**：审计日志服务与 `@audit` 装饰器：
  - `server/app/observability/audit.py`（`AuditService.append()`：向 audit_log 追加记录，trace_id/request_id 嵌入 after JSONB；写入失败 → `UpstreamUnavailable` 503，mutating 操作不得静默成功）。
  - `server/app/common/audit_decorator.py`（`@audit(action=, resource=, load_before=)` 装饰器：捕获 before/after 快照，支持 dict 返回与 `AuditResult` 显式快照；actor 从 logger contextvars 取；资源模板 `{kwarg}` 填充；缺 audit 参数 → TypeError）。
  - 迁移 `0002_timestamps_tz`：T004 修正——把 18 个 naive `DateTime` 列 ALTER 为 `TIMESTAMPTZ`（架构 SSOT 要求；audit_log.ts/evidence_policy.*/sync_state.last_seen_at/baby.current_weight_at/camera_event.occurred_at/sensor_event.received_at/alert.ack_at/derived_baby_state.computed_at/observation_event.*/sleep_session.*/alert_delivery.sent_at/feeding_log.*）。模型同步改 `DateTime(timezone=True)`。
  - 迁移 `0003_audit_append_trigger`：T004 修正——0001 的 `REVOKE UPDATE/DELETE FROM parenting` 对 owner 无效（parenting 是 audit_log owner，隐式持全权限，REVOKE 撤不掉）；挂 BEFORE UPDATE/DELETE trigger 抛异常强制 append-only（owner 也无法绕过，PG append-only 标准做法）。
  - 测试：`test_audit_decorator.py`（9 用例：dict/AuditResult before-after/load_before 钩子/actor 优先级/llm_call_id/写入失败 UpstreamUnavailable/缺参数 TypeError/非 dict 仍记录）+ `test_audit.py`（integration 4 用例：插入字段齐全含 trace_id 嵌入/UPDATE 被拒/DELETE 被拒/写入失败 UpstreamUnavailable）+ `test_migration_apply.py` 增 `test_timestamps_are_timestamptz` 与 trigger 校验，118 passed。
  - 验收：任一接入 `@audit` 的测试 API 调用后有审计记录（decorator 测试覆盖）；审计日志无法通过应用删除（trigger 层强制，集成测试覆盖）。
- **APC-T007**：Auth/RBAC Domain、Repository 与 JWT 服务（进入 Epic E02）：
  - `server/app/auth/domain.py`（`Role` StrEnum：Admin/Caregiver/Viewer/System，对齐架构 §19；`Principal` 鉴权产物；`TokenClaims` JWT claims SSOT：user_id/family_id/role/device_id + iat/exp/jti；`permissions_for` 权限表，P0 Admin 完整、System 自动写入、Caregiver/Viewer 预留 V2；`PasswordHasher`/`JwtService`/`UserRepository` Protocol；`UserRecord`/`FamilyRecord` 结构化协议解耦 ORM）。
  - `server/app/auth/service/password.py`（`Pbkdf2PasswordHasher`：标准库 `hashlib.pbkdf2_hmac` sha256 + 随机 salt，存储 `pbkdf2_sha256$<iter>$<salt_b64>$<digest_b64>`，`hmac.compare_digest` 常量时间比较；不引入 passlib/argon2/bcrypt，最小依赖）。
  - `server/app/auth/service/jwt.py`（`Hs256JwtService`：标准库 hmac/hashlib/base64/json 实现 HS256 JWT，不引入 PyJWT；防 alg=none 降级；解析失败抛 `AuthError` 子类 TokenMalformed/TokenInvalid/TokenExpired/AuthConfig，细分 code 便于审计；缺密钥 fail-fast）。
  - `server/app/auth/service/auth_service.py`（`AuthService`：`authenticate` 登录（用户不存在与密码错统一 AuthError 防枚举）、`issue_token`/`authenticate_token` 往返、`can`/`authorize` RBAC（deny→ForbiddenError 403，未列出动作默认 deny 最小权限）、`create_family`/`create_user`（密码哈希存储、重复 ConflictError、家庭不存在 NotFoundError；mutating 接可选 audit 留痕，T008 gateway 注入启用））。
  - `server/app/auth/infra/repository.py`（`SqlAlchemyUserRepository`：基于 AsyncSession，请求作用域，flush 不 commit，软删除过滤；实现 `domain.UserRepository`）。
  - `server/app/settings.py` 增 `AuthSettings`（jwt_secret/jwt_algorithm/access_ttl_seconds/password_iterations）；`server/app/di.py` 装配 `JwtService`/`PasswordHasher` 无状态单例；`parenting-env.example` 增 `PARENTING_AUTH__*` 样例。
  - 测试：`server/tests/unit/auth/`（test_password 7 + test_jwt 10 + test_auth_service 22，含 RBAC allow/deny、密码哈希、JWT 签发解析篡改/过期/alg=none 防御）+ `server/tests/integration/test_auth.py` 3（端到端建家建人哈希存储、authenticate 成功/失败、JWT 往返），160 passed。
  - 验收：可创建 family/user；Admin 可通过鉴权依赖获得 Principal；非授权角色访问受限方法被拒（ForbiddenError）；密码不得明文存储（PBKDF2）；JWT 含 user_id/family_id/role/device_id。

---

## 3. 进行中

无。APC-T007 已完成，进入 Epic E02（权限、事件、同步与派生状态）。

---

## 4. 下一步

按 MVP 路径（TASK_BACKLOG §4）推进 Epic E02：

1. **APC-T008** — Auth API、设备注册与 seed_family 脚本（依赖 T004,T007；T007 已满足）。
2. **APC-T009** — ObservationEvent Domain、Repository 与幂等写入（依赖 T004,T008）。

---

## 5. 已知风险 / 待办

- `make docs-check` / `make governance-check` 当前为占位提示，待工厂治理脚本接入后替换为真实检查。
- `runtime/` 子目录（db/logs/media/secrets）已存在但被 gitignore；首次使用时由应用按需创建。
- **源码与文档不一致（已解决，2026-08-10）**：`ENGINEERING_DESIGN §9.1` 异常类名与 APC-T002 初版实现命名不同，曾记为分类 C 待裁决。老板已裁决"类名要与 ENGINEERING_DESIGN 对齐"，已重命名为 `ParentingError` 体系并对齐 http_status（`ValidationError` 400、`AuthError` 401/`ForbiddenError` 403、`RuleViolation` 422 + `DoseInterceptError` 子类、`UpstreamUnavailable` 503、`UpstreamTimeout` 504），网关处理器同步更名为 `parenting_error_handler`。详见 DEV_LOG Round 02 与 CHANGELOG [0.2.1]。
- **EventBus 占位**：`InMemoryEventBus` 仅用于 dev/mock 与单测，不跨进程/不持久化/不保证 at-least-once。生产路径 `PgListenEventBus` 在 APC-T003（Alembic 初始化）后落地。
- **worker 注册接口**：`register_worker` 已预留但 APC-T002 不注册任何业务 worker（MQTT/Camera/Normalization/Notification 升级计时在各自任务接入）。
- **本地 PG 库冲突（已解决，2026-08-10 裁决执行）**：本地 `127.0.0.1:5432/parenting` 库曾被兄弟项目 `projects/AI-Parenting-Copilot/` 初始化（29 表 + `alembic_version=0002_event_notify_trigger`）。老板裁决本目录用独立库名 `AI_parenting_dev`，已执行：settings 默认 URL 改为 `…/AI_parenting_dev`、compose `POSTGRES_DB`/`POWERSYNC_DB_NAME` 默认值同步；已建 `AI_parenting_dev` 库并验证 `alembic upgrade head` 干净通过（仅 `alembic_version` 表，无版本记录），与兄弟项目 `parenting` 库完全隔离。
- **`.env.example` harness 拦截（部分解决）**：T003 输出要求"新建 `deploy/.env.example`、修改 `.env.example`"，老板已授权在 `projects/AI-Parenting/` 目录内操作，但 harness 对 `.env*` 文件名硬拦截（Write/Bash mv 均被拒，无法绕过）。已提供等价样例：`deploy/compose-env.example`（Compose 变量样例，请手动 `cp deploy/compose-env.example deploy/.env.example`）与 `parenting-env.example`（应用层 `PARENTING_*` 片段，请手动追加到项目根 `.env.example`）。compose 缺省值已使栈无需 `.env` 可启动，不阻塞功能。
- **文档内部不一致（分类 C，已按 §6.2 实现）**：`ENGINEERING_DESIGN §5.1` ObservationEvent 契约未列 `processing_status`，而 `§6.2` 列出 `processing_status(pending|normalized|projected)`。APC-T004 按 §6.2 实现（`sync_status(pending|synced)` + `processing_status(pending|normalized|projected)`），§5.1 契约为领域层最小集，§6.2 为存储层状态机扩展，两者不冲突。
- **各 *_log 表最小结构（待领域任务细化）**：T004 各 *_log 表（除 feeding_log 外）用最小结构（event_id FK + baby_id + payload jsonb），结构化列留待各领域任务（feeding/diaper/sleep/...）按业务字段细化。feeding_log 已含 P0 端到端结构化列（amount_ml/feeding_type/started_at/ended_at）。
