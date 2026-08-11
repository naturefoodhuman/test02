<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# CHANGELOG —— AI Parenting Copilot 变更日志

> 项目级变更日志，独立于工厂根 `CHANGELOG.md`。
> 格式参考 Keep a Changelog；版本号对应里程碑 / 任务批次。
> Latest Index 在顶部，最新版本在最前。

---

## Latest Index

- [0.9.0] - 2026-08-11 - APC-T009 ObservationEvent Domain、Repository 与幂等写入
- [0.8.0] - 2026-08-11 - APC-T008 Auth API、设备注册与 seed_family 脚本
- [0.7.0] - 2026-08-11 - APC-T007 Auth/RBAC Domain、Repository 与 JWT 服务（进入 Epic E02）
- [0.6.0] - 2026-08-11 - APC-T006 审计日志服务与 @audit 装饰器（含 0002/0003 迁移修正）
- [0.5.0] - 2026-08-11 - APC-T005 结构化日志 / Metrics / Tracing / 健康端点
- [0.4.0] - 2026-08-10 - APC-T004 核心数据库 Schema 初版（28 表 ORM + 初始迁移）
- [0.3.0] - 2026-08-10 - APC-T003 本地基础设施 Docker Compose 与 Alembic 初始化
- [0.2.1] - 2026-08-10 - APC-T002 修订：异常类名对齐 ENGINEERING_DESIGN §9.1
- [0.2.0] - 2026-08-10 - APC-T002 FastAPI 应用壳与公共基础类型
- [0.1.0] - 2026-08-02 - APC-T001 项目骨架初始化

---

## [0.9.0] - 2026-08-11

### Added — APC-T009 ObservationEvent Domain、Repository 与幂等写入

- **`server/app/events/domain/observation_event.py`**（事件溯源核心契约，§5.1 SSOT）：
  - `ObservationEvent` Pydantic 模型（frozen + extra=forbid）：event_id/baby_id/family_id/user_id/device_id/event_type/start_time/end_time/client_created_at/server_received_at/raw_input/normalized_payload/confidence/source/attachments/correction_of/is_deleted + 双状态字段 sync_status/processing_status。
  - `Source`（StrEnum）：manual/voice_text/camera/sensor/ai/system（对齐 ORM CHECK）。
  - `SyncStatus`（StrEnum）：pending/synced（PowerSync 上行状态，§6.2）。
  - `ProcessingStatus`（StrEnum）：pending/normalized/projected（归一化流水线状态，§6.2；以 ORM CHECK 为 SSOT，§5.1 文本 raw|normalized|derived 已在 docstring 记录取舍）。
  - `ObservationEventRepository` Protocol：get/upsert(幂等)/query/soft_delete。
- **`server/app/events/infra/repository.py`**：`SqlAlchemyObservationEventRepository`（基于 AsyncSession，flush 不 commit）。
  - `upsert` 幂等（架构 §505）：event_id 已存在返回既有记录，不创建重复行、不抛 ConflictError。
  - `_to_orm`/`_from_orm`：Pydantic↔ORM 互转集中在本层。
  - `query`：默认排除软删除、按 start_time DESC、支持 baby_id/family_id/event_type 过滤。
  - `soft_delete`：置 is_deleted=true（不物理删除，§5.1）。
- **`server/app/events/service/idempotency.py`**：`EventService`（record/correct/soft_delete）。
  - `record`：event_id 幂等键去重；server_received_at 由注入 Clock 填充（§6.3 服务端权威）；ULID 校验。
  - `correct`：correction 链（§5.1）——软删除旧事件 + 新事件 correction_of 指向旧 event_id（新 event_id 由服务端 new_id 生成）。
  - `soft_delete`：NotFoundError when absent。
  - mutating 方法成功后 `_commit()`（事务边界在 service，§5.2；Fake 替身无 session 跳过）。
  - 可选 `audit: AuditService | None`（T009 无 API 层故 None；T010 gateway 注入启用留痕，§10.4）。
- **`server/tests/unit/events/test_observation_event.py`**：21 项 Pydantic 契约校验。
- **`server/tests/unit/events/test_event_service.py`**：11 项用例（Fake 替身，不依赖 DB）。
- **`server/tests/integration/test_event_repository.py`**：6 项端到端（真实 PG，含 FK 前置建 family+baby）。

### Decisions

- **processing_status 以 ORM 为 SSOT**：枚举值 `pending|normalized|projected` 对齐 ORM CHECK（T004 已迁移），而非 §5.1 文本示例 `raw|normalized|derived`；domain docstring 记录取舍。
- **幂等 upsert 不覆盖既有内容**：纠错走 correction 链而非原地覆盖，保留审计追溯（§5.1）。
- **event_id 由调用方提供**：客户端生成 ULID（架构铁律 8 离线记录不丢失），服务端据此去重；correct 新事件由服务端 new_id 生成。
- **未引入新基础设施**：复用 T004 表、T002 common、T006 AuditService；无新迁移、无新依赖。

### Verified

- ruff / mypy 干净（67 source files）。
- 207 passed（unit 180 + integration 27）。

---

## [0.8.0] - 2026-08-11

### Added — APC-T008 Auth API、设备注册与 seed_family 脚本

- **`server/app/auth/api/routes.py`**（Auth API 路由，§15.2）：
  - `POST /api/v1/auth/login`：家庭+成员名+密码 → access token + Principal 摘要。
  - `POST /api/v1/auth/refresh`：基于有效 access token 滑动续期（P0 简化；V1+ 可引入独立 refresh token）。
  - `POST /api/v1/auth/register-device`：注册设备（需 Admin，§19 device:register），kind=phone/camera/mmwave/mac，fcm_token 存独立字段、meta 存 jsonb。
  - `GET /api/v1/auth/me`：受保护端点示范，返回当前 Principal。
  - 用 `Annotated[T, Depends(...)]` 风格（避免 ruff B008，FastAPI 推荐）。
- **`server/app/auth/domain.py`** 增 `DeviceKind`（StrEnum）、`DeviceRecord` Protocol、`DeviceRepository` Protocol。
- **`server/app/auth/infra/repository.py`** 增 `SqlAlchemyDeviceRepository`（基于 AsyncSession，flush 不 commit）。
- **`server/app/auth/service/auth_service.py`** 增 `register_device`（RBAC authorize device:register，deny→ForbiddenError；可选 audit 留痕）；mutating 方法（create_family/create_user/register_device）成功后 `await self._commit()`（事务边界在 service，§5.2；Fake 替身无 session 时跳过）。
- **`server/app/di.py`** 增 Depends 工厂：`get_session_dep`、`get_auth_service_dep`（请求作用域，注入 UserRepo+DeviceRepo+session+无状态单例）、`get_principal_dep`（从 `Authorization: Bearer <token>` 解析 Principal，缺失/非法→AuthError 401）。
- **`server/app/main.py`** 注册 auth 路由（`app.include_router(auth_router)`）。
- **`server/scripts/seed_family.py`**：本地种子脚本，创建默认家庭+父母 Admin+baby，幂等（按 name/display_name 去重）；`python -m server.scripts.seed_family` 可执行。

### Tests — APC-T008

- `server/tests/integration/test_auth_api.py`（9）：
  - HTTP 流程（dependency_overrides 注入内存替身，避免跨 loop DB 问题）：login→token→/me、错误密码 401、无 token 401、非法 token 401、refresh 新 token、Admin 注册设备 201、Viewer 注册设备 403。
  - DB 写入（纯 asyncio.run + reset_db，与 test_audit 同模式）：register_device 写入 device 表、seed_family 脚本端到端（创建家庭/父母/baby，幂等）。
- 全量 169 passed（135 unit + 34 integration）；ruff/mypy 干净。

### 验收 — APC-T008

- API 前缀 `/api/v1/auth` ✅。
- 设备注册支持 phone/camera/mmwave/mac ✅（DeviceKind 枚举 + DB CHECK 约束）。
- FCM token 存 `device.fcm_token` 独立字段 ✅。
- seed 脚本创建默认 family、父母 Admin、baby 档案 ✅（幂等）。
- Integration：login → token → protected endpoint ✅。
- Integration：device registration 写入 DB ✅。

### 已知简化

- 设备注册的审计留痕待 T009+ 统一 session 管理后接入（避免 audit 与 device 跨 session 的不一致窗口，§10.4）。
- refresh 用 access token 滑动续期（无独立 refresh token / 吊销列表），V1+ 演进。

---

## [0.7.0] - 2026-08-11

### Added — APC-T007 Auth/RBAC Domain、Repository 与 JWT 服务（Epic E02 首任务）

- **`server/app/auth/domain.py`**（领域模型与协议，§2 M02 / §5 / §19）：
  - `Role`（`StrEnum`：Admin/Caregiver/Viewer/System，对齐架构 §19；与 ORM `user.role: String(32)` 直接互转）。
  - `Principal`（鉴权产物，frozen Pydantic；字段与 JWT claims 一一对应：user_id/family_id/role/device_id）。
  - `TokenClaims`（JWT claims SSOT：user_id/family_id/role/device_id + 标准 iat/exp/jti）。
  - `permissions_for(role)` 权限表：P0 Admin 完整权限、System 自动写入派生/告警事件；Caregiver/Viewer 预留 V2（§26.1）；未列出动作默认 deny（最小权限）。
  - `PasswordHasher` / `JwtService` / `UserRepository` Protocol（PEP 544，测试可注入替身）。
  - `UserRecord` / `FamilyRecord` 结构化协议：解耦领域与 ORM，保留 mypy 属性检查。
- **`server/app/auth/service/password.py`**（`Pbkdf2PasswordHasher`，§20 安全）：
  - 标准库 `hashlib.pbkdf2_hmac`（sha256，迭代 310000）+ 随机 salt（16 字节）。
  - 存储格式自洽：`pbkdf2_sha256$<iter>$<salt_b64>$<digest_b64>`，verify 解析回放。
  - `hmac.compare_digest` 常量时间比较，防时序侧信道；不引入 passlib/argon2/bcrypt（最小依赖）。
- **`server/app/auth/service/jwt.py`**（`Hs256JwtService`，§20 令牌鉴权）：
  - HS256（RFC 7519 + RFC 7515），标准库 hmac/hashlib/base64/json，不引入 PyJWT（最小依赖）。
  - `issue(claims)` / `parse(token)`：校验格式（三段）、header alg（防 alg=none 降级）、签名（常量时间）、exp 过期、claims 完整性。
  - 解析失败抛 `AuthError` 子类：`TokenMalformedError` / `TokenInvalidError` / `TokenExpiredError` / `AuthConfigError`（细分 code 便于审计/日志，§22.2）；缺密钥 fail-fast（§8.3）。
- **`server/app/auth/service/auth_service.py`**（`AuthService`，用例层）：
  - `authenticate(family_id, display_name, plain_password, device_id?)`：登录，返回 Principal；家庭不存在 NotFoundError，用户不存在/密码错统一 AuthError（防用户枚举，§20）。
  - `issue_token(principal)` / `authenticate_token(token)`：JWT 签发/解析往返。
  - `can(principal, action)` / `authorize(principal, action)`：RBAC 判定，deny → `ForbiddenError`（403）。
  - `create_family(name, timezone)` / `create_user(family_id, role, display_name, plain_password)`：密码经 PBKDF2 哈希存储；重复 → ConflictError；家庭不存在 → NotFoundError；mutating 接可选 `audit: AuditService | None` 留痕（T008 gateway 注入启用，§10.4）。
- **`server/app/auth/infra/repository.py`**（`SqlAlchemyUserRepository`，§5.2）：
  - 基于 `AsyncSession`，请求作用域；`get_user`/`get_user_by_family`/`get_family`/`create_family`/`create_user`。
  - ULID PK 应用层生成；flush 不 commit（事务边界在 service）；软删除过滤（`is_deleted = false`）。
- **`server/app/settings.py`** 增 `AuthSettings`（`jwt_secret`/`jwt_algorithm`/`access_ttl_seconds`/`password_iterations`）。
- **`server/app/di.py`** 装配 `JwtService` / `PasswordHasher` 无状态单例（跨请求复用）；请求作用域 `UserRepository`/`AuthService` 由 FastAPI Depends 构造。
- **`parenting-env.example`** 增 `PARENTING_AUTH__*` 样例（JWT 密钥/TTL/迭代）。

### Tests — APC-T007

- `server/tests/unit/auth/test_password.py`（7）：正确/错误密码、随机 salt、格式错/算法不匹配、存储格式、多密码参数化。
- `server/tests/unit/auth/test_jwt.py`（10）：issue/parse 往返、device_id=None 保留、篡改签名/ payload、过期、alg=none 伪造防御、格式错、缺密钥 fail-fast、错误是 AuthError 子类。
- `server/tests/unit/auth/test_auth_service.py`（22）：authenticate 成功/家庭不存在/用户不存在/密码错、issue/authenticate_token 往返、RBAC can/authorize（Admin allow、Viewer/Caregiver deny→ForbiddenError、System、未知动作 deny）、create_user 哈希存储/重复 ConflictError/家庭不存在、create_family、audit=None 可用。
- `server/tests/integration/test_auth.py`（3）：端到端建家建人哈希存储、authenticate 成功/失败、JWT 往返（连 AI_parenting_dev）。
- 全量 160 passed（135 unit + 25 integration）；ruff/mypy 干净。

### 验收 — APC-T007

- 可创建 family/user（unit + integration 覆盖）。
- Admin 可通过鉴权依赖获得 Principal（`authenticate` + `authenticate_token`）。
- 非授权角色访问受限方法被拒（`authorize` → ForbiddenError 403）。
- 密码或 PIN hash 不得明文存储（PBKDF2，存储串不含明文，integration 读回验证）。
- JWT 包含 user_id、family_id、role、device_id（TokenClaims SSOT）。
- Auth service 可被 API Gateway 使用（DI 装配 JwtService/PasswordHasher，T008 接入 Depends 工厂）。

---

## [0.6.0] - 2026-08-11

### Added — APC-T006 审计日志服务与 `@audit` 装饰器

- **`server/app/observability/audit.py`**（`AuditService`，§10.4/§22.2）：
  - `append(actor, action, resource, before, after, rule_version, llm_call_id)`：向 `audit_log` 追加一条记录。
  - trace_id/request_id 从 logger contextvars 取，嵌入 `after` JSONB（架构 §6.1 表无 trace_id 列，SSOT 不改）。
  - 写入失败（DB 异常）→ `UpstreamUnavailable`（503），mutating 高风险操作不得静默成功（§10.4）。
  - 仅 append，不提供 update/delete（append-only，迁移层强制）。
- **`server/app/common/audit_decorator.py`**（`@audit` 装饰器，§14.5）：
  - `@audit(action=, resource=, load_before=)` 装饰 mutating API/service 方法。
  - 支持两种返回约定：dict（作为 after 快照）或 `AuditResult`（显式 before/after/rule_version/llm_call_id）。
  - `load_before` 异步钩子提供 before 快照（规则变更前后场景）。
  - actor 从 logger contextvars 取（user_id → device_id → system）。
  - 资源模板 `{kwarg}` 占位填充（如 `"rule/{rule_id}"` → `"rule/01J..."`）。
  - 从被装饰函数签名取 `audit: AuditService` 参数（FastAPI Depends 注入），缺则 TypeError。
- **迁移 `0002_timestamps_tz`**（T004 修正）：18 个 naive `DateTime` 列 ALTER 为 `TIMESTAMPTZ`（架构 SSOT 要求）：
  - audit_log.ts、evidence_policy.effective_from/effective_to、sync_state.last_seen_at、baby.current_weight_at、camera_event.occurred_at、sensor_event.received_at、alert.ack_at、derived_baby_state.computed_at、observation_event.start_time/end_time/client_created_at/server_received_at、sleep_session.started_at/ended_at、alert_delivery.sent_at、feeding_log.started_at/ended_at。
  - 模型同步：`mapped_column(nullable=...)` → `mapped_column(DateTime(timezone=True), nullable=...)`。
- **迁移 `0003_audit_append_trigger`**（T004 修正）：`audit_log` append-only trigger。
  - 0001 的 `REVOKE UPDATE/DELETE FROM parenting` 对 owner 无效（parenting 是 audit_log owner，PG 中 owner 隐式持全权限，REVOKE 撤不掉）——集成测试证实 UPDATE/DELETE 仍可执行。
  - 挂 `BEFORE UPDATE/DELETE` trigger（`parenting_audit_log_append_only()`）抛异常，强制 append-only（owner 也无法绕过，PG append-only 标准做法）。
- **测试**：
  - `server/tests/unit/common/test_audit_decorator.py`（9 用例：dict 返回作 after / AuditResult 显式 before-after / load_before 钩子 / AuditResult.before 覆盖 hook / actor 优先级 / device_id 回退 / llm_call_id 透传 / 写入失败 UpstreamUnavailable / 缺参数 TypeError / 非 dict 仍记录）。
  - `server/tests/integration/test_audit.py`（4 用例：插入字段齐全含 trace_id 嵌入 after / UPDATE 被拒 / DELETE 被拒 / 写入失败 UpstreamUnavailable）。
  - `test_migration_apply.py` 增 `test_timestamps_are_timestamptz` + `test_audit_log_is_append_only` 增 trigger 校验。
  - 118 passed（104 → 118，+14）。

### Fixed

- **T004 naive timestamp 列与架构 SSOT 不一致**：0001 迁移中 18 个时间戳列用 `sa.DateTime()`（无时区），与架构 §6.1 + models/base.py 文档"DB 列用 TIMESTAMP WITH TIME ZONE"不一致。asyncpg 写 timezone-aware datetime 到 naive 列时报 "can't subtract offset-naive and offset-aware datetimes"（T006 AuditService.append 触发）。0002 迁移 ALTER 为 timestamptz，模型同步 `DateTime(timezone=True)`。
- **T004 audit_log append-only 失效**：0001 用 `REVOKE UPDATE/DELETE FROM parenting` 强制 append-only，但 parenting 是 audit_log owner，PG owner 隐式持全权限，REVOKE 撤不掉——UPDATE/DELETE 仍可执行。0003 迁移挂 BEFORE UPDATE/DELETE trigger 抛异常，owner 也无法绕过。

---

## [0.5.0] - 2026-08-11

### Added — APC-T005 结构化日志 / Metrics / Tracing / 健康端点

- **`server/app/observability/logger.py`**（structlog JSON → stdout，§10.1）：
  - `bind_context`/`get_context`/`clear_context`：contextvars 注入全局字段（trace_id/span_id/request_id/family_id/baby_id/user_id/actor_kind/module）。
  - `mask_pii`：递归脱敏——dict 命中 `_SENSITIVE_KEYS`（raw_input/raw/password/auth_hash/token/secret/api_key/fcm_token/access_token/refresh_token）整体替换 `***`；str 跑手机号/邮箱/身份证正则替换 `***`；媒体路径文件名脱敏为 `***`（保留目录结构）；list/tuple 递归元素。
- **`server/app/observability/metrics.py`**（prometheus_client，§10.2）：
  - 指标占位：parenting_record_latency_seconds（Histogram）、voice_normalization_success_ratio（Gauge）、sync_lag_seconds（Gauge）、offline_backfill_success/failed_total（Counter）、alert_delivery_total{level,channel,status}（Counter）、red_alert_delivery_seconds（Histogram）、rule_engine_evaluations_total（Counter）、llm_calls_total{model,status}（Counter）、device_online（Gauge）。
  - `metrics_response_body()`：返回 Prometheus exposition bytes。
- **`server/app/observability/tracing.py`**（OpenTelemetry，§10.3）：
  - no-op tracer 安全降级（dev 不依赖外部 Jaeger）；prod 通过 `PARENTING_OBSERVABILITY__OTEL_EXPORTER_OTLP_ENDPOINT` 启用 OTLP exporter。
  - `current_trace_id()`：从 OTel span context 取 trace_id，与 logger trace_id 贯穿。
- **`server/app/health/api.py`**：
  - `/readyz`：DB ping `SELECT 1`（`check_db`，失败返回 degraded 不抛 500）+ EventBus 状态（`check_event_bus`）；整体 status=ok/degraded。
  - `/metrics`：Prometheus exposition（`text/plain`）。
  - `register_health_routes(app, settings)`：注册 `/readyz` 与 `/metrics`。
- **`server/app/gateway/middleware/logging.py`**（§10.1）：
  - `RequestLoggingMiddleware`：每请求生成 request_id（ULID），入站 `X-Trace-Id` 透传（无则生成 ULID），`bind_context` 注入 contextvars，响应回写 `X-Trace-Id`/`X-Request-Id`，记录 method/path/status/duration_ms，PII 经 `mask_pii` 脱敏，`finally` `clear_context` 防泄漏。
  - `add_request_logging(app)`：注册中间件（类型 `Starlette`，FastAPI 兼容）。
- **`server/app/main.py`** 增补：`_configure_logging(settings)` + `add_request_logging(app)` + `register_health_routes(app, s)` 装配。
- **测试**：
  - `server/tests/unit/common/test_pii_mask.py`（7 用例：敏感 key 整体 `***`、手机号/邮箱/身份证正则、媒体路径文件名、dict/list/tuple 递归、非 str 原样、bind_context 脱敏、clear_context 重置）。
  - `server/tests/integration/test_observability.py`（6 用例：X-Request-Id 回写、X-Trace-Id 入站透传、X-Trace-Id 无则生成、/metrics Prometheus 格式含核心指标名、metrics_response_body helper、/readyz 200 + checks）。
  - 104 passed（91 → 104，+13）。

### Fixed

- **`bind_context` PII 脱敏失效**：原实现对 kwargs 值逐个跑 `mask_pii(v)`（字符串不知 key 名），命中 `_SENSITIVE_KEYS` 的 key（如 `raw_input`）整体脱敏失效——`bind_context(raw_input="宝宝发烧 38.5")` 会泄漏非正则命中的 PII。改为 `mask_pii(dict(kwargs))` 走 dict 分支，命中敏感 key 整体替换 `***`。
- **测试隔离：`/readyz` 跨测试 503**：`test_migration_apply` 用 `asyncio.run`（独立事件循环）跑迁移并 `dispose_db()`，但进程级 `_engine` 缓存遗留绑定到已关闭循环；后续 `test_validation_error_uses_envelope` 的 `/readyz` → `check_db` 拿死连接 → degraded → 503。`tests/conftest.py` `client` fixture 增加 `reset_db()`，每个 TestClient 按当前循环重建 engine。

---

## [0.4.0] - 2026-08-10

### Added — APC-T004 核心数据库 Schema 初版（28 表 ORM + 初始迁移）

- **`server/app/models/`**（base/core/events/logs/derived/rules，按域分文件）：
  - `base.py`：`Base` + `ULIDPrimaryKey`（String(26)）+ `TimestampMixin`（timezone-aware UTC）+ `SoftDeleteMixin`（is_deleted）。
  - 28 张表：family/user/device/baby/observation_event + 13 个 *_log + derived_baby_state/alert/alert_delivery/sleep_session/sensor_event/camera_event + family_knowledge/evidence_policy/audit_log/sync_state。
  - 约束：device.kind/baby.sex/alert.level/alert.status/sleep_session.state/observation_event.source+sync_status+processing_status 枚举 CHECK；evidence_policy(type,region,version) UNIQUE；family_knowledge(family_id,key) UNIQUE；observation_event idx(baby_id,event_type,start_time DESC)。
- **`server/migrations/versions/9dc5086c5ca6_initial_schema.py`**（autogenerate + 手补）：
  - 全表 `updated_at` trigger（`parenting_set_updated_at()` 函数 + 26 表 trigger，表名加双引号规避 `user` 保留字）。
  - `audit_log` REVOKE UPDATE/DELETE FROM PUBLIC/parenting（append-only，§22.2）。
- **`server/migrations/env.py`**：`target_metadata = Base.metadata`。
- **`server/migrations/script.py.mako`**：alembic 官方 async 模板。
- **测试**：`test_models.py`（unit，20+ 用例，表/列/约束/索引/软删除/timestamp 元数据校验）+ `test_migration_apply.py`（integration，4 用例，28 表/26 trigger/audit_log append-only/alembic 版本）。

### 验证

- `make lint`：All checks passed，70 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 68 source files。
- `make test` + integration（pytest）：91 passed。
- 实跑：`alembic upgrade head` 在 `AI_parenting_dev` 成功；29 表、26 trigger、audit_log REVOKE 生效。

### 边界

- 表结构对齐 ENGINEERING_DESIGN §6.1/§6.2 与 §5.1；架构边界/模块职责未改动。
- ULID PK、软删除 partial index、updated_at trigger、audit_log append-only 均按 §6.2/§22.2。
- 未读取/操作 `.env`（红线）；迁移连 `AI_parenting_dev` 独立库。

### 已知不一致（分类 C，已按 §6.2 实现）

- §5.1 ObservationEvent 契约未列 `processing_status`，§6.2 列出 `processing_status(pending|normalized|projected)`。按 §6.2 实现（§5.1 为领域层最小集，§6.2 为存储层状态机扩展，不冲突）。
- 各 *_log（除 feeding_log）用最小结构（event_id + baby_id + payload jsonb），结构化列留待各领域任务细化。

---

## [0.3.0] - 2026-08-10

### Added — APC-T003 本地基础设施 Docker Compose 与 Alembic 初始化

- **`deploy/docker-compose.yml`**：PostgreSQL 15-alpine + Eclipse Mosquitto 2 + PowerSync Service，healthcheck、卷持久化、TZ=UTC，变量 `${VAR:-default}` 缺省值（无 `.env` 亦可启动），对齐 §14 Bootstrap 顺序。
- **`deploy/mosquitto/mosquitto.conf`**：本地 dev 监听 1883、允许匿名、持久化（prod 通过 _infra 注入 ACL+TLS）。
- **`config/powersync/config.yaml` + `sync-rules.yaml`**：PowerSync 配置与空 bucket sync rules 占位（待 APC-T004 Schema 定型后按 §9.2 填充）。
- **`server/app/db.py`**：SQLAlchemy async engine + async_sessionmaker，URL/pool 来自 Settings.database，pool_pre_ping，惰性单例，`get_session` 依赖，`reset_db`/`dispose_db`。
- **`server/migrations/env.py`**：Alembic async env，URL 从 Settings 注入不硬编码，offline/online 双模式，`target_metadata` 占位待 T004。
- **`alembic.ini`**：`script_location=server/migrations`，日志配置。
- **`Makefile`** 增补：`infra-logs`/`infra-reset`/`db-current`/`db-history`/`db-revision`。
- **测试**：`test_db.py`（engine/session factory 惰性/单例/reset/dispose/pool_pre_ping）+ `test_alembic_config.py`（alembic.ini/env.py/compose/配置校验），12 用例。

### 验证

- `make lint`：All checks passed，60 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 59 source files。
- `make test`（pytest）：51 passed。
- 实启动：`docker compose config --services` → postgres/mosquitto/powersync；`alembic current` 可连 PG；`alembic upgrade head --sql` 离线生成正常。

### 边界

- 严格遵守文档优先级；架构边界、模块职责、调用链未改动。
- 复用官方镜像（PostgreSQL/Mosquitto/PowerSync）与社区框架（SQLAlchemy async、Alembic），不自研同步。
- 未读取/操作 `.env` 文件（红线）；compose 缺省值已使栈无需 `.env` 可启动。

### 已知风险（2026-08-10 裁决执行）

- **本地 PG 库冲突（已解决）**：本地 `parenting` 库曾被兄弟项目 `AI-Parenting-Copilot` 占用。老板裁决本目录用独立库名 `AI_parenting_dev`，已改 settings 默认 URL + compose `POSTGRES_DB`/`POWERSYNC_DB_NAME`，建库并验证 `alembic upgrade head` 干净通过，与兄弟项目库隔离。
- **`.env.example` harness 拦截（部分解决）**：老板已授权目录内操作，但 harness 对 `.env*` 文件名硬拦截无法绕过。已提供等价样例 `deploy/compose-env.example` + `parenting-env.example`，请老板手动 `cp deploy/compose-env.example deploy/.env.example` 并将 `parenting-env.example` 追加到根 `.env.example`。compose 缺省值已使栈无需 `.env` 可启动。

---

## [0.2.1] - 2026-08-10

### Changed — APC-T002 修订：异常类名对齐 ENGINEERING_DESIGN §9.1

应老板裁决"类名要与 ENGINEERING_DESIGN 对齐"，将 `server/app/common/errors.py` 异常层次重命名并对齐 http_status（§9.1 为异常命名 SSOT）：

- `DomainError` → **`ParentingError`**（基类，500）。
- `ValidationError` http_status 422 → **400**（§9.1；领域业务校验）。
- `UnauthorizedError` → **`AuthError`**（401）；`ForbiddenError` 改为 **`AuthError` 子类**（403），保留 401/403 区分。
- `RuleViolationError` → **`RuleViolation`**（422）；新增 **`DoseInterceptError(RuleViolation)`**（剂量拦截，422）。
- `InfrastructureError` → 拆为 **`UpstreamUnavailable`**（503）+ **`UpstreamTimeout`**（504）。
- 网关 `domain_error_handler` → **`parenting_error_handler`**（`server/app/gateway/exception_handlers.py`）。

### 验证

- `make lint`：All checks passed，56 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 55 source files。
- `make test`（pytest）：39 passed（新增 `test_forbidden_error_is_auth_error_subclass`、`test_dose_intercept_is_rule_violation_subclass`）。

### 边界

- 仅重命名与 http_status 对齐，未改架构边界/模块职责/调用链。
- 统一信封 `{code,message,evidence,trace_id}` 不变。
- 领域层 `ValidationError`（业务校验）= 400；FastAPI `RequestValidationError`（schema 校验）仍 422（网关独立处理），两者语义不同，不冲突。

---

## [0.2.0] - 2026-08-10

### Added — APC-T002 FastAPI 应用壳、Settings、DI 与公共基础类型

- **`server/app/common/ids.py`**：ULID 生成（`new_id`/`is_valid_ulid`/`parse_ulid`），26 字符 Crockford base32，时间有序，复用 `python-ulid`。
- **`server/app/common/clock.py`**：timezone-aware UTC 时钟（`Clock` Protocol + `SystemClock` + `ensure_aware`），`@runtime_checkable`，测试可注入替身。
- **`server/app/common/errors.py`**：领域异常层次（`ParentingError` + 子类，对齐 §9.1）+ `ErrorEnvelope{code,message,evidence,trace_id}`，领域层不感知 HTTP。
- **`server/app/common/repository.py`**：`Repository[T]` Protocol（`get`/`upsert`/`query`），`@runtime_checkable`。
- **`server/app/common/event_bus.py`**：PG LISTEN/NOTIFY 协议（`EventBus`）+ `InMemoryEventBus` 占位（dev/mock）。
- **`server/app/settings.py`**：pydantic-settings，`PARENTING_` 前缀 + `__` 嵌套，分层加载，聚合 7 个子配置域，`env` 校验，`lru_cache` 单例。
- **`server/app/di.py`**：进程级 `Container` + 惰性单例 + FastAPI `Depends` 工厂。
- **`server/app/gateway/exception_handlers.py`**：全局异常处理器，领域异常 → HTTP + 统一错误信封，含 422/404/500 兜底。
- **`server/app/main.py`**：`create_app` 工厂 + 模块级 `app` 单例；lifespan（Container 装配 + EventBus 启停 + worker 调度）；`/healthz` + `/readyz`；`register_worker` 接口预留。
- **测试**：`server/tests/conftest.py` + `server/tests/unit/common/*`（7 文件）+ `server/tests/integration/test_healthz.py`，37 passed。

### 验证

- `make lint`（ruff check + format --check）：All checks passed，52 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 52 source files。
- `make test`（pytest）：37 passed。
- 实启动：`uvicorn server.app.main:app` 可启动，`/healthz` 200，OpenAPI 可访问，404 统一信封，dev 无 DB 可启动。

### 边界

- 严格遵守文档优先级；架构边界、模块职责、调用链未改动。
- 复用社区成熟实现，不重复造轮子。
- 未读取/操作 `.env` 文件（红线）。
- 未配置 DB 时 dev/mock 模式可启动并清晰提示（APC-T002 验收标准）。

### 已知不一致（分类 C，已于 [0.2.1] 对齐解决）

- `ENGINEERING_DESIGN §9.1` 异常类名与 APC-T002 初版实现命名不同（语义等价），已于 [0.2.1] 按老板裁决对齐 §9.1。

---

## [0.1.0] - 2026-08-02

### Added — APC-T001 项目骨架与工程元数据

- **目录结构**：`server/app/`（21 领域子模块）、`server/migrations/`、`server/scripts/`、`server/tests/`（unit/integration/golden/security/e2e）、`android/`、`firmware/esp32c6/`、`config/`、`deploy/`、`tests/`、`runtime/`。
- **`pyproject.toml`**：Python 3.11+ 依赖与工具链（ruff / mypy / pytest）配置。
- **`Makefile`**：lint / typecheck / test / security-test / golden / rules-validate / infra-up / db-migrate / run-dev / docs-check / governance-check 等目标。
- **`.env.example`**：PARENTING_ 前缀分层加载样例，无真实密钥。
- **`.gitignore`**：runtime/、.env、密钥、媒体、缓存、Android/固件构建产物忽略；保留 .gitkeep 与 fixtures。
- **`README.md`**：项目入口、SSOT 文档表、快速开始、命令、目录结构、边界说明。
- **`docs/PROJECT_STATE.md`**：当前状态 SSOT 与任务状态索引。
- **`docs/DEV_LOG.md`**：开发日志。
- **`docs/CHANGELOG.md`**：本文件。
- **`docs/ADR/ADR-001-project-bootstrap.md`**：骨架决策记录。
- **占位 `__init__.py`**：`server/` 全包（含各领域子包、migrations、scripts、tests 子目录），仅文件头注释，待 APC-T002 起填充。
- **`runtime/.gitkeep`**：确保 runtime/ 入库但内容被忽略。

### 验证

- `make lint` 通过（空 `__init__.py` 不触发 ruff 报错）。
- `make docs-check` 通过（占位提示 + PROJECT_STATE 任务索引 grep）。

### 边界

- 不碰 `projects/AI-Parenting-Copilot/`。
- 不写工厂根 docs。
- 不复制工厂 `_infra/` 实现。
