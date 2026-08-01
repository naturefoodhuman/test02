<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-01 01:22:00
-->


# PROJECT_STATE —— AI Parenting Copilot 当前状态 SSOT

**更新日期**：2026-08-01 CST
**当前阶段**：P0-M1 DB-backed API runtime hardening + PG worker/Normalization/State pipeline 继续开发
**当前任务状态**：新增 Scheduler periodic worker 与 Backup restore drill planner；`APC-T036/T044` 代码继续推进但仍等待生产规则审查/真实 NAS restore drill；累计 DONE 以 `docs/TASK_BACKLOG.md` 顶部状态行为准。
**状态说明**：本文件是 AI Parenting Copilot 项目级当前状态 SSOT；工厂根目录文档仅作为工厂能力与治理规则参考。下方较早轮次的“阻塞原因”段落保留为历史审计记录；若与本节或 `docs/TASK_BACKLOG.md` 顶部状态冲突，以本节和 `TASK_BACKLOG.md` 为准。

---

## 0. 2026-07-31 当前验证基线与本轮进展

### 用户 Mac 验收

- `make db-integration-test` 在用户 Mac + PostgreSQL 环境已通过：`5 passed, 1 warning in 3.97s`。
- 该结果确认 DB-backed Auth/Event/Alert/Rules/State API smoke、repository adapter、audit 写入与 migration head 可运行。

### 本轮修复

- 修复 `make test` 在 shell 中保留 `PARENTING_DATABASE__URL` 时误切换到 PostgreSQL repo 的问题：
  - `Makefile test` 显式 `env -u PARENTING_DATABASE__URL -u PARENTING_DATABASE_URL`。
  - `tests/conftest.py` 对非 `integration` 测试自动隔离 DB env，直接运行 pytest 也保持 dev-mock。
- 新增 `make api-db-smoke-test`，可单独运行 DB-backed API runtime smoke：`tests/integration/test_api_db_runtime.py`。
- `server/scripts/seed_family.py` 从纯 in-memory 升级为双模式：无 DB URL 时输出 dev seed；有 `--database-url` 或 `PARENTING_DATABASE__URL` 时通过 SQLAlchemy Auth adapter 持久化 family/admin/baby。
- 清理 `pyproject.toml` 中重复的 `sqlalchemy[asyncio]` 依赖，保留 `sqlalchemy[asyncio]>=2.0`。























### 继续开发进展（Android background drain / mmWave list API）

- 新增 Android native `BackgroundDrainJobService`、`BackgroundDrainScheduler`、`BootReceiver`、`ApiSettingsStore`、`ApiSettingsActivity`，使用 JobScheduler 定时/手动 drain pending events 与 local alert acks。
- `MainApplication` 自动 schedule periodic drain；`MainActivity` 提供 API Settings / Drain 入口。
- `GET /api/v1/mmwave/devices/{device_id}/events` 支持查询 sensor events，dev/DB mode 均可用。

### 继续开发进展（Android native API drains）

- 新增 `NativeApiClient.kt`，为 native fallback screens 提供最小 POST JSON client。
- 新增 `PendingSyncDrainer.kt`，将 native SQLite pending events POST 到 `/api/v1/events`，成功后 `markSynced()`。
- 新增 `AlertAckDrainer.kt`，将 native alert ack actions POST 到 `/api/v1/alerts/{id}/ack`。
- `AlertActionReceiver` 支持 `drainLocalActions()`；`PendingEventsActivity` 增加“Drain pending to server”按钮。
- Static tests 覆盖 native API client/drainers 与 TS drain contracts。

### 继续开发进展（Android pending sync / alert ack drains）

- 新增 `android/src/sync/pending_sync_drain.ts`：将 native pending local events POST 到 `/api/v1/events`，成功后调用 native `markSynced()`。
- 新增 `android/src/notification/ack_drain.ts`：drain native alert ack actions，调用 `/api/v1/alerts/{id}/ack`，成功后停止本地 fallback。
- Static tests 覆盖 pending event drain 与 local alert action drain contracts，继续推进 `APC-T047/T048/T052`。

### 继续开发进展（Camera/mmWave ingest APIs）

- 新增 `server/app/mmwave/api/routes.py`：`POST /api/v1/mmwave/frames`，解析 radar frame，写入 `sensor_event`，可选生成 sensor `ObservationEvent`，并写 `mmwave.frame_ingest` audit。
- Camera API 新增 `POST /api/v1/camera-events` 与 `GET /api/v1/sleep-sessions/{session_id}/camera-events`，DB mode 写入 `camera_event` 并写 `camera_event.create` audit。
- `tests/integration/test_api_db_runtime.py` 扩展 mmWave ingest + camera event API DB smoke；`tests/test_mmwave_api.py` / `tests/test_camera_adapters.py` 覆盖 dev route。

### 继续开发进展（Camera/mmWave DB repositories）

- 新增 `SQLAlchemySensorEventRepository`，支持 mmWave `SensorEventCandidate` 写入 `sensor_event` 并按 device 查询。
- 新增 `SQLAlchemyCameraEventRepository`，支持 camera shadow events 写入 `camera_event` 并按 session/camera 查询。
- `tests/integration/test_db_repository_adapters.py` 扩展 sensor_event/camera_event DB smoke，推进 `APC-T038/T039/T040`。

### 继续开发进展（Scheduler worker / Backup restore drill）

- 新增 `PeriodicSchedulerWorker`，FastAPI lifespan 注册 scheduler worker；默认不 run-on-start，避免 dev/test 副作用。
- Scheduler worker 保留 run snapshot：run_count、last_started_at、last_finished_at、last_error、last_results。
- 新增 `RestoreDrillPlanner` / `BackupManifest`，可生成 `pg_restore` dry-run plan、restore manifest 和 verification steps。
- 新增 `docs/BACKUP_RESTORE_RUNBOOK.md` 和 `make restore-dry-run`。

### 继续开发进展（Sleep / Media / Export DB API smoke）

- Sleep Session API 已支持 DB mode：`SQLAlchemySleepSessionRepository` 实现 start/pause/resume/end/set_roi，API mutating 操作写 audit。
- Media API DB mode 已写入 `media_asset` 并写 `media.upload` audit；读取支持从 DB metadata 恢复 record。
- 新增 Export API：`POST /api/v1/exports/summary`、`GET /api/v1/exports/{id}`，导出 MD/PDF placeholder 并写 `export.summary` audit。
- `tests/integration/test_api_db_runtime.py` 已扩展 Sleep/Media/Export DB smoke；等待用户 Mac `make api-db-smoke-test` 复验后推进 T037/T042/T043。

### 继续开发进展（Scheduler API）

- 新增 `server/app/scheduler/api/routes.py`，提供 `GET /api/v1/scheduler/jobs`、`POST /api/v1/scheduler/jobs/{job}/trigger`、`POST /api/v1/scheduler/trigger-all`。
- FastAPI app 现在初始化 `SchedulerRunner`，注册 morning brief、supplement、health check、vaccine due jobs。
- Scheduler API 触发会写 audit（DB mode 使用 request audit，dev mode 使用 MemoryAuditSink）。
- 根据用户 `make api-health-smoke` 真实环境通过，`APC-T035` 标记 DONE。

### 运维说明修复（FastAPI 启动）

- 补充 `docs/RUNBOOK_LOCAL_API.md`，明确三终端启动/验证流程：infra、FastAPI、curl/health smoke。
- 新增/完善 Make targets：`make run-api`、`make api-health-smoke`、`make api-server-smoke-test`。
- `server/scripts/run_dev.sh` 启动时打印 DB/PowerSync env、API URL、下一步 health smoke 提示；仅在 DB URL 存在时自动迁移。
- 该修复回应用户 curl 8000 失败场景：curl 前必须在单独终端启动 `make run-api`。

### 继续开发进展（Health probes / system health check）

- 新增 `server/app/health/probes/`：Database, TCP, HTTP, PowerSync health probes。
- FastAPI app DB mode 会注册 database probe；默认注册 MQTT TCP probe；配置 `PARENTING_POWERSYNC__URL` 时注册 PowerSync probe。
- `/api/v1/system/health` 现在返回 latest device/service health snapshot，并在有 offline probe 时返回 degraded。
- 新增 `POST /api/v1/system/health/check` 可手动运行 probes，并沿用 DeviceHealthMonitor 生成 gray alert。
- 新增 tests：`tests/test_health_probes.py`, `tests/test_health_api_probes.py`。

### 继续开发进展（Android Quick Record native offline write）

- 新增 `QuickRecordActivity.kt`，可在 native shell 中保存 feeding event 到 `LocalEventStore.insertPending()`，实现 Android 端本地写入先成功的 P0 兜底路径。
- 新增 `PendingEventsActivity.kt`，展示 pending sync 数量和最近 pending events，便于真机验证离线记录未丢失。
- `MainActivity.kt` 从纯 TextView 改为 native shell launcher，提供 Quick Record / Pending Sync / Critical Alert Demo 入口。
- Android manifest 注册 QuickRecord/PendingEvents activities；static tests 已覆盖。

### 继续开发进展（Android auth/session + local sync native skeleton）

- 新增 Android Keystore-backed `SecureSessionStore.kt` 与 TS `native_secure_session.ts` bridge contract，推进 `APC-T046`。
- 新增 native SQLite `LocalEventStore.kt` / `LocalObservationEvent.kt` 与 TS `native_sqlite_bridge.ts`，支持 local pending event insert/pending/markSynced，推进 `APC-T047`。
- 根据用户已确认 `./gradlew assembleDebug BUILD SUCCESSFUL`，`APC-T045` 已标记 DONE；新增 native files 仍需下一轮用户 Android build 复验。

### 继续开发进展（Android Gradle bootstrap）

- 修复用户本地 `cd android/android && ./gradlew assembleDebug` 报 `no such file or directory`：新增 `android/android/gradlew`、`gradlew.bat`、`gradle/wrapper/gradle-wrapper.properties`。
- `gradlew` 支持：优先 committed wrapper jar；其次系统 `gradle`；否则 macOS/Linux 下下载配置的 Gradle distribution 到 gitignored `.gradle/bootstrap/`。
- 新增 `make android-native-build`，等价于 `cd android/android && ./gradlew assembleDebug`。
- `.gitignore` 补充 `android/android/.gradle/`、`android/android/build/`、`android/android/app/build/`。

### 继续开发进展（Android native critical alert）

- 新增 Android native trigger-only alert payload、full-screen critical alert activity、local alert action receiver、notification channel helper。
- Android manifest 注册 `CriticalAlertActivity` 和 `AlertActionReceiver`，并在 `MainApplication` 启动时创建 notification channels。
- 新增 TS `native_bridge.ts`，定义 full-screen/ack fallback bridge contract。
- Static tests 覆盖 native files、trigger-only payload、showWhenLocked/turnScreenOn、IMPORTANCE_HIGH 与 bridge routing。

### 继续开发进展（Notification cancel / escalation support）

- `NotificationOrchestrator.cancel()` 已实现 channel cancel 并写入 cancellation delivery receipts。
- `POST /api/v1/alerts/{alert_id}/ack` 现在会在 ack 后调用 channel cancel，并写入 `alert.cancel_channels` audit。
- 新增 `GET /api/v1/alerts/{alert_id}/deliveries`，便于 App/测试读取 delivery/cancel receipts。
- 根据用户上一轮本地复验通过，`APC-T029` 已标记 DONE。

### 继续开发进展（Notification channels / DB delivery）

- 新增安全默认 notification adapters：`FCMChannel`、`MacSpeakerChannel`、`AppFullscreenChannel`、`CameraSpeakerChannel` 与 `build_default_channels()`。
- 新增 `POST /api/v1/alerts/{alert_id}/dispatch`：按 alert level 扇出默认通道，并在 DB mode 下通过 `SQLAlchemyDeliveryRepository` 写入 `alert_delivery`。
- `tests/integration/test_api_db_runtime.py` 扩展 alert dispatch → delivery receipts → audit smoke；下一步需用户 Mac `make api-db-smoke-test` 复验后推进 `APC-T032/T033` 状态。

### 继续开发进展（Dose Interceptor DB audit）

- 新增 `server/app/observability/sqlalchemy_audit_sink.py`，让 `DoseInterceptor` 可在请求事务内写入真实 `audit_log`。
- `/api/v1/copilot/query` DB mode 现在为 Orchestrator 注入 `SQLAlchemyAuditSink`，不再退回 memory-only audit。
- `tests/integration/test_api_db_runtime.py` 扩展 dose intercept → `audit_log` smoke；下一步需用户 Mac `make api-db-smoke-test` 复验后解除 `APC-T029` 阻塞。
- 根据用户已通过的 DB-backed Memory/Orchestrator 复验，同步 `APC-T026/T027/T028` 为 DONE；根据规则测试和前置解除，同步 `APC-T020/T021` 为 DONE。

### 继续开发进展（Memory / Orchestrator）

- 新增 `server/app/memory/sqlalchemy_store.py`：从 PostgreSQL 构建 M1-M5 MemorySnapshot，包含 baby hard facts、family_knowledge、DerivedBabyState baseline、近 72h short context、当前 EvidencePolicy rule versions。
- 新增 `server/app/memory/local_rag.py`：薄适配工厂 Local RAG store/search 结果，不复制工厂实现。
- `ContextBuilder` 支持 async memory store；Orchestrator DB mode 通过 API route 注入 `SQLAlchemyMemoryStore`。
- `LoggerCopilot` 复用 Normalization voice parser，Quick Record 候选与后台归一化保持一致。
- `tests/integration/test_api_db_runtime.py` 扩展 DB memory smoke；下一轮需用户 Mac `make api-db-smoke-test` 复验。

### 用户 Mac worker 链路验收通过

- 用户确认新增 `make worker-db-smoke-test` / DB smoke / API smoke / `make test` 验证通过。
- 据此解除 `APC-T011/T013/T014/T015/T016/T017` 的主要 DB/worker 验收阻塞并标记 DONE。
- `make powersync-smoke-test` 与 `server/app/sync/service/powersync_probe.py` 已通过用户 Mac PowerSync liveness/config 复验，`APC-T012` 已标记 DONE。

### 继续开发进展（live worker smoke）

- 新增 `make worker-db-smoke-test`，运行 `tests/integration_worker/test_event_normalization_worker.py`，用于用户 Mac 上验证真实 `events.changed` LISTEN/NOTIFY worker 能把 API 写入的 feeding event 自动归一化并写入 `DerivedBabyState`。
- `SQLAlchemyStateSnapshotRepository.upsert()` 现在会将 `source_event_count` 同步持久化到 `derived_baby_state.snapshot`，DB API 读取时不再丢失来源事件数量。
- 普通 `make test` 因新增 integration worker smoke 现在为 `144 passed, 6 deselected, 1 warning`；worker smoke 单独执行，避免常规 DB repository suite 变慢/变脆。

### 本轮 DB 集成回归修复（EvidencePolicy idempotency）

- 用户 Mac `make db-integration-test` 暴露 `evidence_policy(policy_type, region, version)` 重复激活同一规则包时唯一键冲突。
- 修复 `server/app/rule_engine/sqlalchemy_evidence_repo.py`：`activate()` 对同一 `policy_type/region/version` 改为幂等返回/复活已有记录；仅在新版本激活时关闭其他 current 版本。
- 扩展 `tests/integration/test_db_repository_adapters.py`：同一 medication rule pack 连续 activate 两次应返回同一 hash，并保持 current 可读。

### 继续开发进展（PG worker / Normalization / State）

- 新增 `server/app/normalization/sqlalchemy_store.py`：P0 derived tables（feeding/diaper/sleep/temperature/supplement）SQLAlchemy upsert/read，按 `event_id` 做 PostgreSQL `ON CONFLICT` 幂等写入。
- 新增 `server/app/normalization/worker.py`：`PendingEventProcessor`、`process_pending_events()`、`PostgresEventNormalizationWorker`；支持 `events.changed` LISTEN/NOTIFY 后 drain pending events。
- `server/app/main.py` 在 DB mode 下注册 `PostgresEventNormalizationWorker` 到既有 `WorkerRegistry`。
- `server/app/state_engine/sqlalchemy_snapshot_repo.py` 改为 PostgreSQL `ON CONFLICT` upsert，避免 worker 并发时 `derived_baby_state` 主键冲突。
- `tests/integration/test_api_db_runtime.py` 扩展 DB-backed event→normalization→state smoke；无 DB URL 沙盒仍按 integration skip。

### 本轮状态变更

- `APC-T008`：BLOCKED → DONE（Auth API、设备注册、seed_family DB/in-memory 双模式、DB-backed smoke 验收）
- `APC-T010`：BLOCKED/缺失状态 → DONE（Events API dev + DB-backed adapter/audit smoke 验收）
- `APC-T019`：BLOCKED → DONE（Rules Admin validate/activate/admin gate + DB-backed EvidencePolicy/audit smoke 验收）
- `APC-T031`：BLOCKED → DONE（Alert create/list/ack/feedback + SQLAlchemy repo/audit smoke 验收）

### 沙盒验证

```bash
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 161 passed, 8 deselected, 1 warning
make lint
make typecheck
make db-integration-test
# 无 DB URL：5 skipped
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
make docs-check
make api-db-smoke-test
# 无 DB URL：1 skipped
```

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


### APC-T009 — 实现 ObservationEvent 契约、Repository 与幂等写入

状态：BLOCKED

已完成代码/单元验证：

- `server/app/events/domain/observation_event.py`：ObservationEvent Pydantic 契约、EventSource、SyncStatus、ProcessingStatus、timezone-aware 校验。
- `server/app/events/service/idempotency.py`：event_id 幂等身份校验与冲突检测。
- `server/app/events/infra/repository.py`：EventRepository Protocol 与 InMemoryEventRepository，支持 upsert/get/list/soft_delete/correct。
- 测试覆盖合法同步契约、naive datetime 拒绝、重复 upsert 幂等、冲突检测、纠错链与软删除。

阻塞原因：DB-backed repository 与重复 upsert 的 PostgreSQL 集成验收待 Docker/PostgreSQL 环境。

### APC-T010 — 实现 Events API：创建、查询、纠错、软删除

状态：BLOCKED

已完成代码/测试：

- `server/app/events/api/routes.py`：`POST /api/v1/events`、`GET /api/v1/events`、`GET /api/v1/events/{event_id}`、`POST /api/v1/events/{event_id}/correct`、`DELETE /api/v1/events/{event_id}`。
- `server/app/main.py`：dev/in-memory EventRepository 与 MemoryAuditSink 注入，events router 注册。
- 测试覆盖 create/list/correct/delete 流程与 MemoryAuditSink 审计记录。

阻塞原因：当前 API 为 dev/in-memory 模式；真实 DB repository、PowerSync 契约与 audit_log 持久化集成验收待 PostgreSQL。


### APC-T018 — 实现 Rule Engine Kernel、Loader、Registry 与 EvidencePolicy Repo

状态：BLOCKED

已完成代码/验证：

- `server/app/rule_engine/domain/models.py`：RuleInput、RuleResult、EvidenceItem、Verdict。
- `server/app/rule_engine/loader.py`：YAML RulePack 加载、schema 校验、hash 计算、`rules-validate` CLI。
- `server/app/rule_engine/registry.py`、`kernel.py`：RuleModule registry 与 RuleEngine façade。
- `server/app/rule_engine/evidence_repo.py`：InMemoryEvidencePolicyRepository，支持 activate/current/cache invalidation。
- `make rules-validate` 通过。

阻塞原因：EvidencePolicy PostgreSQL 持久化与规则变更 audit_log 集成验收待 Docker/PostgreSQL。

### APC-T020 — 实现 Medication Rule Domain 与黄金测试

状态：BLOCKED

已完成代码/验证：

- `server/app/rule_engine/domains/medication.py`：MedicationRuleModule。
- `config/rules/medication/base.yaml`：dev 规则包。
- `tests/golden/rules/medication_cases.yaml` 与 `tests/test_medication_rules.py`。
- 覆盖未知体重、未知浓度、<6 月龄布洛芬、间隔/24h 上限与剂量计算；剂量仅由 RuleResult.outputs 输出。

阻塞原因：前置 `APC-T018` 尚待 DB/audit 验收，规则包医学内容也需生产前临床审查。

### APC-T021 — 实现 Triage 与 Alert Threshold Rule Domain

状态：BLOCKED

已完成代码/验证：

- `server/app/rule_engine/domains/triage.py`：3 月龄以下 ≥38°C 红色分诊规则、危险信号规则。
- `server/app/rule_engine/domains/thresholds.py`：趋势双条件规则、mmWave 单信号禁止红警。
- `config/rules/triage/base.yaml`、`config/alert_thresholds.yaml`。
- `tests/golden/rules/triage_cases.yaml` 与 `tests/test_triage_threshold_rules.py`。

阻塞原因：前置 `APC-T018`、`APC-T016` 未 DONE；State Engine 派生输入与真实告警联动待后续任务。


### APC-T022 — 实现 Vaccine Planner Rule Domain

状态：BLOCKED

已完成代码/验证：

- `server/app/rule_engine/domains/vaccine.py`：VaccineRuleModule，可根据 birth_date/as_of/records 生成疫苗 due_date/status/evidence。
- `config/rules/vaccine/cn-nip-2024.yaml`：CN NIP dev fixture 规则包。
- `tests/golden/rules/vaccine_cases.yaml` 与 `tests/test_vaccine_rules.py`。
- 覆盖出生当天计划、逾期、completed/skipped 记录状态。

阻塞原因：前置 `APC-T018` 未 DONE；疫苗规则包为 dev fixture，生产前需官方免疫规划审查与 EvidencePolicy DB/audit 验收。

### APC-T023 — 实现 Growth Rule Domain 与 WHO 百分位基础

状态：BLOCKED

已完成代码/验证：

- `server/app/rule_engine/domains/growth.py`：GrowthRuleModule，可按 sex/age_months/metric/value 返回 percentile_band/evidence。
- `config/rules/growth/who-0-5.yaml`：简化 WHO-compatible fixture。
- `tests/golden/rules/growth_cases.yaml` 与 `tests/test_growth_rules.py`。
- 单点成长测量不产生强告警，输出 `alert_level=none`。

阻塞原因：前置 `APC-T018` 未 DONE；P0 当前使用简化 fixture，完整 WHO LMS 表与生产规则审查待后续任务/验收。


### APC-T026 — 实现 Memory Store M1-M5 与 Local RAG 适配

状态：BLOCKED

已完成代码/验证：

- `server/app/memory/injector.py`：MemorySnapshot 与 in-memory MemoryStore，覆盖 M1 硬事实、M2 家庭偏好、M3 baseline、M4 短期上下文、M5 纠错记忆结构。
- 测试覆盖 M1-M5 snapshot 构建。

阻塞原因：前置 `APC-T016` 未完成；真实 DerivedBabyState/FamilyKnowledge/Local RAG 适配待后续集成。

### APC-T027 — 实现 Copilot Base、Registry 与 Logger Copilot

状态：BLOCKED

已完成代码/验证：

- `server/app/copilots/base.py`：DomainCopilot Protocol、CopilotRequest、CopilotResponse、CopilotRegistry。
- `server/app/copilots/logger_copilot.py`：P0 Logger Copilot，支持中文喂奶/尿布/体温文本解析，仅输出 `record_candidate`，不写 DB，requires_confirmation=true。
- 测试覆盖 “刚喂了90ml奶” 生成 feeding candidate、未知输入低置信、registry 选择。

阻塞原因：前置 `APC-T026` 未 DONE；完整 LLM ModelClient 注入与 Quick Record 联动待后续。

### APC-T028 — 实现 Orchestrator、Intent Router、Context Builder 与 Output Guard

状态：BLOCKED

已完成代码/验证：

- `server/app/orchestrator/intent_router.py`：record/question/triage/config/alert_ack 意图路由。
- `server/app/orchestrator/context_builder.py`：基于 MemoryStore 构建 MemorySnapshot。
- `server/app/orchestrator/output_guard.py` 与 `orchestrator.py`：dev Orchestrator façade。
- `server/app/orchestrator/api/routes.py`：`POST /api/v1/copilot/query` dev API。
- `server/app/main.py`：dev Orchestrator 注入与 router 注册。
- 测试覆盖 intent routing 与 copilot query → logger candidate。

阻塞原因：前置 `APC-T027` 与 `APC-T006` 未 DONE；真实 Memory/DB/audit 集成待验收。

### APC-T029 — 实现 Dose Interceptor 与安全回归测试

状态：BLOCKED

已完成代码/验证：

- `server/app/orchestrator/dose_interceptor.py`：匹配 mg/ml/毫升/滴/片 等剂量模式，LLM/Copilot free text 替换为固定安全话术。
- Rule Engine 标记的结构化 dose 可通过。
- MemoryAuditSink 审计记录 `dose_intercept`。
- 测试覆盖 prompt injection 风格剂量输出拦截、Rule Engine 剂量通过、审计 sink 写入。

阻塞原因：前置 `APC-T028` 未 DONE；真实 audit_log DB 写入待 PostgreSQL 验收。


### APC-T030 — 实现 P0 Copilots：Proactive、FamilyMemory、Vaccine、Growth、Medication Basic

状态：BLOCKED

已完成代码/验证：

- `server/app/copilots/proactive_copilot.py`：ProactiveCopilot，生成 reminder_candidates，不自行生成告警等级。
- `server/app/copilots/family_memory.py`：FamilyMemoryCopilot，生成 memory_update candidate，requires_confirmation=true。
- `server/app/copilots/vaccine_planner.py`：VaccinePlannerCopilot，通过 VaccineRuleModule 输出 rule_result/evidence。
- `server/app/copilots/growth_milestone.py`：GrowthMilestoneCopilot，通过 GrowthRuleModule 输出 percentile/evidence。
- `server/app/copilots/medication_safety.py`：MedicationSafetyCopilot，通过 MedicationRuleModule 输出结构化 rule_engine dose 结果。
- `server/app/orchestrator/orchestrator.py` 默认 registry 注册 P0 Copilots，可通过显式 intent 调用。
- `tests/test_p0_copilots.py` 覆盖各 Copilot 输出结构、evidence、requires_confirmation 与 registry。

阻塞原因：前置 `APC-T020/T022/T023/T028/T029` 均未 DONE；FamilyMemory 真实写入、Memory/RAG、DB/audit 与 App/API 集成待后续验收。


### APC-T031 — 实现 Alert Repository、API、确认与反馈

状态：BLOCKED

已完成代码/验证：

- `server/app/notification/alert_repo.py`：AlertRecord、Create/Ack/Feedback request、AlertLevel、AlertStatus、FeedbackType、InMemoryAlertRepository。
- `server/app/notification/api/routes.py`：`/api/v1/alerts` create/list/get/ack/feedback dev API。
- `server/app/main.py`：dev alert repository 注入与 alert router 注册。
- 测试覆盖 create → list → ack → feedback，并通过 MemoryAuditSink 记录 alert.create/alert.ack/alert.feedback。

阻塞原因：前置 `APC-T004/T006/T021` 未 DONE；真实 alert DB repository 与 audit_log 持久化待 PostgreSQL 验收。

### APC-T032 — 实现 Notification Channel 抽象与 FCM/Mac/App/Camera 通道

状态：BLOCKED

已完成代码/验证：

- `server/app/notification/channels/base.py`：NotificationChannel Protocol 与 DeliveryReceipt。
- `server/app/notification/channels/fake.py`：FakeFCM、FakeMacSpeaker、FakeAppFullscreen、FakeCameraSpeaker 通道。
- `config/notification.yaml`：P0 channel config skeleton。
- 测试覆盖 FCM-like payload 仅包含 alert_id/level/type，敏感 evidence/recommended_action 不出 payload；通道失败返回 failed receipt。

阻塞原因：前置 `APC-T031` 未 DONE；真实 FCM/TTS/摄像头扬声器通道待后续接入与设备验收。

### APC-T033 — 实现 Notification Orchestrator 扇出与 Delivery Receipt

状态：BLOCKED

已完成代码/验证：

- `server/app/notification/orchestrator.py`：按 Alert.level 选择通道、red/orange 多通道扇出、FCM 失败不阻断 Mac/App fallback。
- `server/app/notification/delivery_repo.py`：InMemoryDeliveryRepository。
- 测试覆盖 red alert 多通道 delivery receipts 与失败隔离。

阻塞原因：前置 `APC-T032` 未 DONE；真实 alert_delivery DB 持久化与升级状态机待后续验收。


### APC-T034 — 实现告警升级状态机与确认取消

状态：BLOCKED

已完成代码/验证：

- `server/app/notification/escalation.py`：EscalationStateMachine，支持 0s 初始扇出、60s Mac repeat、90s phone/camera escalation、ack cancel。
- `FakeNotificationChannel.cancel()` dev cancel hook。
- `tests/test_escalation.py`：虚拟时间 advance 与 ack 后不再升级。

阻塞原因：前置 `APC-T033` / `APC-T034` / `APC-T035` / `APC-T036` / `APC-T037` / `APC-T038` / `APC-T039` / `APC-T040` / `APC-T041` / `APC-T042` / `APC-T043` / `APC-T044` / `APC-T054` / `APC-T055` / `APC-T057` / `APC-T045` / `APC-T046` / `APC-T047` / `APC-T048` / `APC-T058` 未 DONE；真实 channel cancel、升级计时 worker 与 audit_log 集成待验收。

### APC-T035 — 实现 Device Health Monitor 与灰色告警

状态：BLOCKED

已完成代码/验证：

- `server/app/health/monitor.py`：HealthProbe Protocol、MockHealthProbe、DeviceHealthMonitor。
- mock probe offline 时生成 `level=gray` / `type=device_health` 告警。
- `/api/v1/system/health` dev response 预留 `device_health` snapshot。
- `tests/test_device_health_monitor.py` 覆盖 probe failure → gray alert。

阻塞原因：真实 DB/MQTT/PowerSync/Camera/mmWave/FCM/NAS probes 与 DB alert 持久化待验收。

### APC-T036 — 实现 Scheduler：晨报、疫苗到期、补剂提醒、健康巡检

状态：BLOCKED

已完成代码/验证：

- `server/app/scheduler/runner.py`：manual-trigger SchedulerRunner。
- jobs：`morning_brief.py`、`vaccine_due.py`、`supplement.py`、`health_check.py`。
- `tests/test_scheduler_jobs.py` 覆盖手动触发、疫苗 due、补剂提醒、健康巡检。

阻塞原因：前置 `APC-T022/T031/T035` 未 DONE；FastAPI 同进程 worker/真实 schedule/audit/DB 持久化待接入。


### APC-T037 — 实现 Sleep Session Domain/API 与 ROI 配置

状态：BLOCKED

已完成代码/验证：

- `server/app/camera/sleep_session.py`：SleepSessionState 与 InMemorySleepSessionRepository，支持 start/pause/resume/end 与 analysis_allowed gate。
- `server/app/camera/roi.py`：ROIConfig。
- `server/app/camera/api/routes.py`：sleep session start/pause/resume/end/roi dev API。
- `server/app/main.py`：dev sleep session repository 注入与 camera router 注册。
- `tests/test_sleep_session.py` 覆盖状态机合法/非法转换、ROI 与 API flow。

阻塞原因：前置 `APC-T004/T006` 未 DONE；真实 sleep_session DB repository 与 mutating audit_log 持久化待 PostgreSQL 验收。

### APC-T038 — 实现 Camera RTSP/ISAPI/Fregata 桥接与 Snapshot Mock

状态：BLOCKED

已完成代码/验证：

- `server/app/camera/rtsp_client.py`：MockRTSPSnapshotClient 返回 PNG snapshot。
- `server/app/camera/isapi_client.py`、`fregata_bridge.py`：真实适配入口 placeholder。
- `config/devices.yaml`：dev camera/mock 与 mmWave topic 配置。
- `GET /api/v1/cameras/{camera_id}/snapshot` dev mock API 返回 image/png。
- `tests/test_camera_adapters.py` 覆盖 devices.yaml 解析与 mock snapshot API。

阻塞原因：前置 `APC-T037/T035` 未 DONE；真实 RTSP/ISAPI/Fregata 与设备健康断线回退待设备环境验收。


### APC-T039 — 实现 Clip Recorder、多信号 Fusion 与 VLM Dispatcher 影子模式

状态：BLOCKED

已完成代码/验证：

- `server/app/camera/clip_recorder.py`：ClipRecorder 与前 15s / 后 30s clip plan。
- `server/app/camera/fusion.py`：FusionStateMachine，确保仅 active sleep session 内分析、mmWave 单信号仅 shadow、不产生红色强提醒。
- `server/app/camera/vlm_dispatcher.py`：通过注入 Model Gateway compatible vision client 进行 shadow dispatch。
- `tests/test_camera_shadow_pipeline.py` 覆盖 inactive session、mmWave-only shadow、多信号 shadow、VLM dispatcher 使用注入 client。

阻塞原因：前置 `APC-T021/T038/T040` 未 DONE；真实 camera_event DB 写入、媒体 clip 录制与本地 VLM/ModelGateway 集成待验收。

### APC-T040 — 实现 mmWave Frame Parser、Sensor Mapper 与 MQTT Subscriber

状态：BLOCKED

已完成代码/验证：

- `server/app/mmwave/frame_parser.py`：RadarFrame 与 JSON/JSONL parser。
- `server/app/mmwave/sensor_event_mapper.py`：SensorEventCandidate 与 ObservationEventCreate candidate mapper。
- `server/app/mmwave/mqtt_subscriber.py`：topic whitelist 与 message handler skeleton。
- `tests/fixtures/radar_frames.jsonl` 与 `tests/test_mmwave_parser.py` 覆盖 fixture parser、sensor mapping、ObservationEvent candidate、topic whitelist。

阻塞原因：真实 Mosquitto/MQTT subscriber、DB sensor_event / observation_event 入库与 reconnect 行为待 Docker/PostgreSQL 环境验收。


### APC-T042 — 实现加密 Media Storage、Thumbnail 与 Media API

状态：BLOCKED

已完成代码/验证：

- `server/app/media/storage.py`：AES-GCM encrypted local file store、MediaAssetRecord、in-memory asset index。
- `server/app/media/thumbnails.py`：Pillow thumbnail generation。
- `server/app/media/api/routes.py`：JSON/base64 dev upload 与 read API。
- `server/app/main.py`：dev MediaStorageService 注入与 media router 注册。
- `tests/test_media_storage.py` 覆盖加解密 roundtrip、密文不含明文、thumbnail 与 API upload/read。

阻塞原因：前置 `APC-T004/T006` 未 DONE；真实 media_asset DB 持久化、audit_log 与生产文件密钥管理待验收。

### APC-T043 — 实现 Export MD/PDF 与就诊摘要基础

状态：BLOCKED

已完成代码/验证：

- `server/app/media/export/markdown.py`：Markdown summary renderer。
- `server/app/media/export/pdf.py`：PDF placeholder renderer。
- `server/app/export/service.py`：local export service，生成 MD/PDF placeholder files 与 ExportRecord。
- `tests/test_export_service.py` 覆盖 7d/visit summary markdown 与 PDF placeholder 输出。

阻塞原因：前置 `APC-T016/T042` 未 DONE；真实事件/派生态查询、导出 audit_log 与下载授权待后续集成。


### APC-T041 — 实现 ESP32C6 mmWave MQTT 固件基础

状态：BLOCKED

已完成代码/验证：

- `firmware/esp32c6/platformio.ini`：XIAO ESP32C6 + Arduino + PubSubClient skeleton。
- `firmware/esp32c6/src/main.cpp`：mock payload MQTT publisher，字段包含 presence/state/breathing_rate/heart_rate/abnormal_event/timestamp。
- `firmware/esp32c6/config.h.example`：无真实 WiFi/MQTT 密钥。
- `firmware/esp32c6/README.md`：配置、构建、payload 说明。
- `tests/test_firmware_skeleton.py`：静态验证 payload fields 与 secret placeholder。

阻塞原因：前置 `APC-T040` 未 DONE；当前环境无 PlatformIO/真实 ESP32C6，`pio run` 与硬件发布待验收。

### APC-T044 — 实现 Backup：PG dump、媒体归档、launchd 与恢复演练文档

状态：BLOCKED

已完成代码/验证：

- `server/app/backup/pg_dump_task.py`：PGDumpTask dry-run plan 与 pg_dump command。
- `server/app/backup/media_archive.py`：MediaArchiveTask dry-run plan，归档 encrypted files/thumbs。
- `deploy/launchd/com.parenting.backup.plist`：launchd 示例。
- `docs/RUNBOOK_BACKUP_RESTORE.md`：备份/恢复演练文档。
- `make backup-dry-run`：输出 dry-run backup plans。
- `tests/test_backup_tasks.py`：备份路径、命令、保留 encrypted media 策略测试。

阻塞原因：前置 `APC-T003/T042` 未 DONE；真实 `pg_dump`、NAS 路径与恢复演练待 Mac 环境验收。


### APC-T054 — 实现开发启动脚本、launchd plist 与部署样例

状态：BLOCKED

已完成代码/文档：

- `server/scripts/run_dev.sh`、`run_worker.sh`。
- `deploy/launchd/com.parenting.server.plist`、`com.parenting.fregata.plist`。
- `docs/RUNBOOK_DEPLOYMENT.md`。
- `make backup-dry-run` 与部署/启动文档入口。

阻塞原因：前置 `APC-T003/T036/T044` 未 DONE；真实 launchd、infra bootstrap 与 Fregata binary 配置待 Mac 环境验收。

### APC-T055 — 实现 Dev Fixtures、Fake Services 与 Mock Publishers

状态：BLOCKED

已完成代码/验证：

- `tests/fixtures/model_responses/logger_candidate.json`、`tests/fakes.py`。
- `server/scripts/mock_mmwave_publisher.py`：dry-run print 与 optional aiomqtt publish。
- `tests/fixtures/radar_frames.jsonl` 已带 `_forge_trace`。
- `make security-test` 与 `make e2e-fake-test` 复用 fake services。

阻塞原因：前置 `APC-T032/T038/T040` 未 DONE；真实 MQTT integration 与设备级 fixture 验收待后续。

### APC-T057 — 实现红色告警 E2E：生成 → 多通道 → 升级 → Ack 停止

状态：BLOCKED

已完成代码/验证：

- `tests/e2e/test_red_alert_delivery.py`：server-side fake red alert delivery/escalation/ack regression。
- 验证 fake FCM/Mac/App/Camera 多通道、虚拟时间升级、ack cancel。

阻塞原因：前置 `APC-T021/T034/T052/T055` 未 DONE；Android notification E2E 与真实设备 ack 流程待实现。

### APC-T058 — 建立安全回归套件：Dose、Prompt Injection、PII、Canary、审计不可删除

状态：BLOCKED

已完成代码/验证：

- `tests/security/test_prompt_injection.py`：LLM/prompt injection 剂量输出拦截。
- `tests/security/test_privacy_regression.py`：PII redaction、canary block、raw media cloud block。
- `tests/security/test_audit_immutability_static.py`：audit_log trigger/revoke 静态回归。
- `make security-test`：当前 5 passed。

阻塞原因：前置 `APC-T006/T029/T031` 未 DONE；真实 DB audit update/delete 被拒集成测试待 PostgreSQL 验收。


### APC-T045 — 初始化 React Native Android-only 应用壳、主题、导航与 API Client

状态：BLOCKED

已完成代码/验证：

- `android/package.json`：Android-only React Native dependency skeleton。
- `android/src/App.tsx`：App shell。
- `android/src/api/client.ts`：base URL、Bearer token、healthz/post helpers。
- `android/src/navigation/routes.ts` 与 `android/src/theme/colors.ts`。
- `android/README.md`、`android/tsconfig.json`。
- `tests/test_android_skeleton.py` 覆盖 package/API/theme/navigation static checks。

阻塞原因：真实 RN native Android/Gradle 工程与 `assembleDebug` 待 Android toolchain 验收。

### APC-T046 — 实现 Android Auth、家庭切换与设备注册

状态：BLOCKED

已完成代码/验证：

- `android/src/state/session.ts`：SessionState 与 reducer。
- `android/src/features/auth/authService.ts`：login 与 device registration API flow。
- static tests 覆盖 `/api/v1/auth/login`、`/devices/register`、FCM token mapping。

阻塞原因：前置 `APC-T045/T008` 未 DONE；安全存储、native integration 与真实 server DB device persistence 待验收。

### APC-T047 — 实现 Android op-sqlite + PowerSync Schema 与 pending_sync

状态：BLOCKED

已完成代码/验证：

- `android/src/sync/schema.ts`：LocalObservationEvent 同步契约字段。
- `android/src/sync/local_event_store.ts`：InMemoryLocalEventStore，insert 即 `pending_sync=true`。
- `android/src/sync/powersync_client.ts`：PowerSync config skeleton。

阻塞原因：前置 `APC-T012/T046` 未 DONE；op-sqlite/PowerSync native integration 与设备端离线写入验收待后续。

### APC-T048 — 实现 Android Quick Record P0

状态：BLOCKED

已完成代码/验证：

- `android/src/features/quick_record/recordCandidate.ts`：feeding/temperature/diaper/unknown candidate builder。
- `android/src/features/quick_record/createLocalEvent.ts`：confirmed candidate → local ObservationEvent payload。
- static tests 覆盖 “90ml” feeding payload、requiresConfirmation 与 pending_sync 由 store 负责。

阻塞原因：前置 `APC-T027/T047` 未 DONE；真实 UI、大按钮、语音文本、一次确认和本地 SQLite 写入待 Android toolchain 验收。


### APC-T049 — 实现 Android Today 首页

状态：BLOCKED

已完成代码/验证：`android/src/features/today/viewModel.ts`，展示 feeding/diaper/sleep/pending_sync/device health/active alerts 的 view model；static tests 已覆盖。

阻塞原因：前置 `APC-T016/T035/T047` 未 DONE；真实 RN UI 与 PowerSync 副本读取待验收。

### APC-T050 — 实现 Android Timeline

状态：BLOCKED

已完成代码/验证：`android/src/features/timeline/viewModel.ts`，支持 day grouping、source display、correction payload、soft delete payload、5 分钟重复 feeding soft hint；static tests 已覆盖。

阻塞原因：前置 `APC-T010/T012/T047` 未 DONE；真实 UI 编辑/撤销与审计链路待验收。

### APC-T051 — 实现 Android Alert Center

状态：BLOCKED

已完成代码/验证：`android/src/features/alert_center/viewModel.ts`，支持 evidence rows、ack API、feedback API 与 feedback enum；static tests 已覆盖。

阻塞原因：前置 `APC-T031/T046` 未 DONE；真实 UI 与 server DB ack/feedback 持久化待验收。

### APC-T052 — 实现 Android Notification

状态：BLOCKED

已完成代码/验证：`android/src/notification/*` 与 `android/src/background/work_manager.ts`，支持 FCM trigger-only payload、alert detail REST fetch、高优先级 channel config、FullScreenIntent 权限引导、本地兜底、background sync work request；static tests 已覆盖。

阻塞原因：前置 `APC-T034/T051` 未 DONE；真实 FCM/Notifee/native FullScreenIntent/WorkManager 待 Android 设备验收。

### APC-T053 — 实现 Android Sleep Session UI 与 ROI 配置

状态：BLOCKED

已完成代码/验证：`android/src/features/sleep_session/viewModel.ts`，支持 active-only analysisVisible、shadow mode label、ROI save API；static tests 已覆盖。

阻塞原因：前置 `APC-T037/T038/T039` 未 DONE；真实 RN UI/snapshot/ROI 手势待验收。


### APC-T013 — 实现 Normalization 表单/语音文本解析与领域派生表写入

状态：BLOCKED

已完成代码/验证：`server/app/normalization/*`，支持 voice/form feeding/diaper/sleep/temperature/supplement 归一化、event_id lineage 与 in-memory derived store。

阻塞原因：前置 `APC-T011` 未完成；真实 DB 派生表写入待验收。

### APC-T014 — 实现去重、纠错链处理与 Normalization Worker

状态：BLOCKED

已完成代码/验证：`scan_pending`、feeding dedup helper、correction chain helper；重复 pending 事件不会重复写入 in-memory derived store。

阻塞原因：真实 PG LISTEN/NOTIFY worker、pending recovery scan 与 DB 派生表更新待验收。

### APC-T015 — 实现 Baby State Engine P0 Projection

状态：BLOCKED

已完成代码/验证：feeding/diaper/sleep/temperature/supplement projection pure functions；测试覆盖顺序无关的稳定 DerivedBabyState 输出。

阻塞原因：前置 `APC-T013` 未 DONE；DB 集成待验收。

### APC-T016 — 实现 State Engine 增量重算、Snapshot Repo 与 State API

状态：BLOCKED

已完成代码/验证：`BabyStateEngine`、`InMemoryStateSnapshotRepository`、`GET /api/v1/babies/{baby_id}/state` dev API。

阻塞原因：前置 `APC-T015/T006` 未 DONE；真实 `derived_baby_state` DB upsert 与 auth/audit 集成待验收。

### APC-T017 — 打通 Event → Normalization → State 集成链路

状态：BLOCKED

已完成代码/验证：dev/in-memory integration test 覆盖 event API write → normalization → state recompute → state API read。

阻塞原因：前置 `APC-T010/T014/T016` 未 DONE；真实 PG event bus、PowerSync、DB 派生链路待验收。


### APC-T011 — 实现 PG LISTEN/NOTIFY 事件总线与事件变更触发器

状态：BLOCKED

已完成代码/验证：

- `server/app/common/event_bus.py` 增加 PgNotifyPayload、parse_pg_notify_payload、domain_event_from_pg_notify。
- `server/migrations/versions/0002_event_notify_trigger.py` 增加 observation_event INSERT/UPDATE/DELETE notify trigger。
- `tests/test_event_bus_notify.py` 覆盖 payload parse 与 migration static checks。

阻塞原因：真实 PostgreSQL LISTEN/NOTIFY worker、at-least-once 消费与启动日志待 Docker/PostgreSQL 环境验收。

### APC-T012 — 实现 PowerSync 适配、同步契约校验与冲突软提示基础

状态：BLOCKED

已完成代码/验证：

- `server/app/sync/service/contract_validator.py`：同步契约字段校验、source/confidence 校验、5 分钟重复 feeding 软提示。
- `server/app/sync/infra/powersync_config.yaml`：family observation/state stream config skeleton。
- `tests/test_sync_contract.py` 覆盖缺字段拒绝、合法记录与 duplicate feeding soft hint。

阻塞原因：真实 PowerSync service 读取配置、Android sync 写入与非法事件拦截链路待集成验收。

### APC-T019 — 实现规则 Admin API：validate / activate / audit

状态：BLOCKED

已完成代码/验证：

- `server/app/rule_engine/api/routes.py`：`GET /api/v1/rules/validate`、`POST /api/v1/rules/activate`。
- Admin gate 使用 dev `x-role: Admin` header。
- 激活规则包写入 InMemoryEvidencePolicyRepository 并通过 MemoryAuditSink 记录 `rule.activate`。
- `tests/test_rules_admin_api.py` 覆盖 validate、非 Admin 拒绝、Admin activate 与 audit。

阻塞原因：前置 `APC-T018/T008` 未 DONE；真实 EvidencePolicy DB persistence、auth dependency 与 audit_log 持久化待验收。


### APC-T056 — 实现 MVP E2E：离线 Feeding 记录 → 同步 → 派生态回传

状态：BLOCKED

已完成代码/文档：

- `tests/e2e/test_mvp_feeding_roundtrip.md`：半自动 MVP Feeding Roundtrip checklist。
- `android/e2e/mvp_feeding.e2e.ts`：Detox placeholder。
- dev substitute 已由 `tests/test_event_to_state_pipeline.py` 覆盖 server-side Event → Normalization → State。

阻塞原因：前置 `APC-T017/T047/T048/T049/T055` 未 DONE；真实 Android offline/PowerSync/Today E2E 待设备与 DB 环境验收。

### APC-T059 — 建立 Shadow/Soak/Harden 验证与发布检查清单

状态：BLOCKED

已完成代码/文档：

- `tests/shadow/camera_mmwave_shadow_harness.py`：mock camera/mmWave shadow harness，可输出 false_positive_rate。
- `tests/soak/locustfile.py`：family-scale 1 req/s Locust skeleton，未安装 locust 时仍可静态导入。
- `docs/RELEASE_CHECKLIST_P0.md`：覆盖 infra、安全、告警、camera/mmWave shadow、Android MVP、备份恢复。
- `tests/test_shadow_soak_release.py`：shadow harness / locustfile / checklist smoke tests。
- `make shadow-test`：生成 runtime/shadow_report.json。

阻塞原因：前置 `APC-T039/T054/T057/T058` 未 DONE；真实 7 晚 shadow 数据、soak 趋势与发布前人工 checklist 待执行。

---

## 4. 当前未实现

- PostgreSQL / Mosquitto / PowerSync / Alembic 代码配置已接入，但容器运行验收尚未完成，归属 `APC-T003 BLOCKED`。
- 核心 Schema、审计、Auth/API、ObservationEvent/Event API 代码已完成但集成验收 BLOCKED；Rule Engine 各 P0 规则域纯逻辑已部分完成但集成验收 BLOCKED；Android 等尚未开始。

---

## 5. 最新验证基线

在 `projects/AI-Parenting-Copilot/` 下运行：

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 120 source files
make test
# 127 passed, 1 warning
python3 -m uvicorn server.app.main:app --host 127.0.0.1 --port 8765
# /healthz smoke: HTTP 200
```

仓库根目录额外治理检查：`make docs-check` → `Blockers: 0; Warnings: 1`。该 warning 为架构敏感词提示，本轮未改变架构边界。

---

## 6. 下一步

最高优先级任务：

- Task ID：`APC-T003` / `APC-T004` / `APC-T006` / `APC-T007` / `APC-T008` / `APC-T009` / `APC-T010` / `APC-T018` / `APC-T020` / `APC-T021` / `APC-T022` / `APC-T023` / `APC-T026` / `APC-T027` / `APC-T028` / `APC-T029` / `APC-T030` / `APC-T031` / `APC-T032` / `APC-T033` / `APC-T034` / `APC-T035` / `APC-T036` / `APC-T037` / `APC-T038` / `APC-T039` / `APC-T040` / `APC-T041` / `APC-T042` / `APC-T043` / `APC-T044` / `APC-T054` / `APC-T055` / `APC-T057` / `APC-T045` / `APC-T046` / `APC-T047` / `APC-T048` / `APC-T058`
- 任务名称：完成 Docker/PostgreSQL 相关集成验收与 DB-backed Auth/Event 持久化
- 状态：BLOCKED，等待具备 Docker CLI 的环境执行 `make infra-up`、`make db-migrate`、迁移升降级、audit_log immutability、Auth/Event DB repository / seed DB 写入验证。

可并行候选：继续实现不依赖真实 DB 的事件契约、Rule Engine 纯逻辑或测试 fake，但不得把依赖 PostgreSQL 集成验收的任务标记 DONE。


## 7. DB-backed repository adapter progress

状态：部分完成，仍 BLOCKED 待 PostgreSQL 集成验收。

已新增 SQLAlchemy adapters：

- `server/app/auth/infra/sqlalchemy_repository.py`
- `server/app/events/infra/sqlalchemy_repository.py`
- `server/app/notification/sqlalchemy_alert_repo.py`

这些 adapters 为解除 `APC-T007/T008/T009/T010/T031` 的 DB 持久化阻塞做准备；当前通过 mypy/ruff/static tests，但尚未在真实 PostgreSQL transaction 中验收，因此对应任务状态不变。


### Additional DB-backed repository adapter progress

状态：部分完成，仍 BLOCKED 待 PostgreSQL 集成验收。

本轮新增 SQLAlchemy adapters：

- `server/app/state_engine/sqlalchemy_snapshot_repo.py`
- `server/app/rule_engine/sqlalchemy_evidence_repo.py`
- `server/app/media/sqlalchemy_media_repo.py`
- `server/app/notification/sqlalchemy_delivery_repo.py`
- `server/app/camera/sqlalchemy_sleep_session_repo.py`

这些 adapters 为解除 `APC-T016/T018/T032/T037/T042` 的 DB 持久化阻塞做准备；当前通过 mypy/ruff/static tests，但尚未在真实 PostgreSQL transaction 中验收，因此对应任务状态不变。


## 8. DB integration harness

状态：已新增，等待用户 Mac/PostgreSQL 环境执行。

新增：

- `tests/integration/test_db_repository_adapters.py`
- `make db-integration-test`

覆盖：

- Alembic upgrade head（基于 `PARENTING_DATABASE__URL`）。
- Auth/Event/State/Alert/Delivery/Media/SleepSession repository adapters 在 PostgreSQL transaction 中 CRUD。
- Auth DB device/list/get-by-display-name。
- Event DB idempotent upsert/correction/soft delete。
- EvidencePolicy activation。
- observation_event PG `events.changed` NOTIFY trigger emits event_id/baby_id/operation。
- audit_log UPDATE 被 DB trigger 拒绝。
- Alembic upgrade/downgrade/upgrade roundtrip on a temporary PostgreSQL database.

默认 `make test` 排除 `integration` marker；无 DB URL 时 `make db-integration-test` 自动 skip。


## 9. Media package tracking fix

已修复 `.gitignore` 的 `media/` 递归忽略问题，`server/app/media/` 源码包已纳入 Git 跟踪。该修复解决用户侧 `ModuleNotFoundError: server.app.media` 集成测试导入失败。


## 10. Temporary migration database admin URL fix

用户 Mac 验收发现 `test_alembic_upgrade_downgrade_roundtrip_on_temporary_database` 连接 maintenance database `postgres` 时，`parenting` 用户认证失败。已修复为使用已验证可登录的应用数据库连接作为 admin connection target，再创建/删除临时数据库。该修复不改变架构，只调整 integration test harness 对本地 Docker volume/role 的兼容性。


## 11. DB integration URL password rendering fix

用户 Mac 验收发现 migration roundtrip test 即使连接应用库 `parenting`，仍然报 `InvalidPasswordError`。根因是 SQLAlchemy `URL.__str__()` 默认隐藏密码为 `***`，integration harness 将隐藏后的 URL 传给 asyncpg。已改为 `render_as_string(hide_password=False)`，并新增 regression test `tests/test_db_integration_url_rendering.py`，确保临时 DB URL 不含 `***`。


## 12. DB integration validation accepted

用户 Mac 集中验收已通过：

```bash
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
make infra-up
make db-migrate
make db-current
make db-integration-test
# 4 passed
```

据此解除以下任务的 DB/migration/audit 阻塞并标记 DONE：

- `APC-T003`：本地基础设施 Docker Compose 与 Alembic 初始化。
- `APC-T004`：核心数据库 Schema 初版。
- `APC-T006`：审计日志服务与 `@audit` 装饰器基础。
- `APC-T007`：Auth/RBAC Domain、Repository 与 JWT 服务。
- `APC-T009`：ObservationEvent 契约、Repository 与幂等写入。
- `APC-T018`：Rule Engine Kernel、Loader、Registry 与 EvidencePolicy Repo。

仍保持 BLOCKED 的原因：API runtime 尚有部分 dev/in-memory wiring、PowerSync/worker/Android/硬件/生产规则审查尚未完成。


## 13. DB-backed runtime wiring progress

状态：部分完成，仍等待用户 Mac DB integration 复验。

已完成：

- `server/app/main.py` 在 `PARENTING_DATABASE__URL` 存在时创建 async SQLAlchemy engine/session factory。
- HTTP middleware 为每个请求注入 `request.state.db_session` 并按响应状态 commit/rollback。
- Auth API、Events API、Alert API、Rules Admin API 可在请求级 db_session 存在时使用 SQLAlchemy repositories，否则保持 dev in-memory fallback。
- `SQLAlchemyAlertRepository` 补齐 `list_active`，支持 Alert API DB mode。

下一次用户验收 `make db-integration-test` 通过后，可继续增加 DB-backed API integration tests。


## 14. Android native skeleton progress

状态：部分完成，仍 BLOCKED 待 Android toolchain/RN integration 验收。

新增 native Android skeleton：

- `android/android/settings.gradle`
- `android/android/build.gradle`
- `android/android/app/build.gradle`
- `android/android/app/src/main/AndroidManifest.xml`
- `android/android/app/src/main/java/com/aiparentingcopilot/MainActivity.kt`
- `android/android/app/src/main/java/com/aiparentingcopilot/MainApplication.kt`

该 skeleton 用于让“安卓手机端应用程序”有明确 native 工程入口。当前仍是最小 Android shell，React Native bridge、Gradle wrapper、真实 native modules 与设备构建需后续 Android toolchain 验收。


## 15. DB-backed API runtime integration harness

状态：已新增，等待用户 Mac/PostgreSQL 环境执行。

新增：

- `tests/integration/test_api_db_runtime.py`

覆盖：

- FastAPI runtime 在 `PARENTING_DATABASE__URL` 存在时注入 request-level SQLAlchemy session。
- Auth API DB mode：init-family、device registration。
- Events API DB mode：create/list。
- Alert API DB mode：create/ack。
- Rules Admin API DB mode：activate unique temporary rule pack。
- State API DB mode：读取 `derived_baby_state` snapshot。

`make db-integration-test` 现在无 DB URL 时 5 skipped；用户 Mac DB 环境应执行 5 个真实 integration tests。


## 16. DB-backed API runtime test isolation fix

用户 Mac 验收发现 `test_db_backed_auth_event_alert_state_and_rules_api` 在 teardown 阶段尝试 rollback 已关闭 transaction，并且 state snapshot seeding 误用 pytest fixture function `engine`。已修复：

- DB-backed API runtime integration test 改为显式使用 `engine` fixture，不再在外部 fixture transaction 中手动 commit。
- 测试通过 API 创建 family/admin，再通过独立 DB session 为同一 family seed baby。
- 测试结束后按 family_id 清理相关 DB 数据，避免污染持久化开发库。
- State snapshot seeding 使用 `async_sessionmaker(engine, ...)` 的真实 AsyncEngine fixture。


## 17. Request-level DB audit wiring

状态：已新增，等待用户 Mac DB integration 复验。

新增：

- `server/app/observability/request_audit.py`

修复与增强：

- Auth/Event/Alert/Rules API 在 DB mode 下可将 audit records 写入 `audit_log`，dev mode 仍 fallback 到 MemoryAuditSink。
- `test_api_db_runtime.py` 修复 transaction isolation：使用真实 AsyncEngine fixture、独立 session seed、按 family_id 清理数据。
- API runtime integration test 新增 audit row 断言，覆盖 auth/event/alert/rule audit actions。


## 18. Final handoff checkpoint before context compaction

已更新 `docs/HANDOFF.md` 为下一 Agent 的最新入口。重点：

- Android app 位于 `projects/AI-Parenting-Copilot/android/`。
- DB integration harness 最新目标是 `make db-integration-test` = `5 passed`。
- 当前最新修复为 request-level DB audit wiring 和 API DB runtime integration isolation。
- 下一 Agent 应先复验用户 Mac 上 `make db-integration-test` 结果，再决定是否解除更多 BLOCKED。


## 19. User-reported bugfix round

用户指出并已处理的问题：

- `Makefile` Alembic targets 改为 uv-first：`uv run --active python -m alembic ...`。
- `pyproject.toml` SQLAlchemy dependency 改为 `sqlalchemy[asyncio]>=2.0`。
- `project_feeding` 现在按真实 rolling 24h window 统计，不再对全部 feeding 记录求和。
- `voice.py` P0 parser 支持更多常见中文顺序：如 `80 毫升奶`、`奶 80 毫升`、`体温 39.5 ℃`。
- Orchestrator 不再重复构造相同 `CopilotRequest`。
- Vaccine/Growth/Medication Copilot 改为 lazy-load rule packs，并基于文件所在位置解析项目根绝对路径，避免从仓库根运行 pytest 时因相对路径出错，也避免构造 Orchestrator 时立即做 rule-pack I/O。
- `request_audit.py` 语法修正并保持 DB/dev audit fallback 正常。

验证：`make test` → `140 passed, 5 deselected, 1 warning`。
