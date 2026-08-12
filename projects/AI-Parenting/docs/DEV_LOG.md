<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# DEV_LOG —— AI Parenting Copilot 开发日志

> 项目级开发日志，独立于工厂根 `DEV_LOG.md`。每轮开发记录一条。
> Latest Index 在顶部，最新一轮在最前。

---

## Latest Index

- 2026-08-12 · Round 12 · APC-T012 PowerSync 适配半成品修复（contract_validator mypy 修复 + 文档补齐 T010/T011 外部记忆）
- 2026-08-12 · Round 11 · APC-T011 PG LISTEN/NOTIFY 事件总线与事件变更触发器补记（代码 2026-08-11 已落地，本轮补文档）
- 2026-08-12 · Round 10 · APC-T010 Events API 补记 + T007 JwtService.parse 时钟不对称修复（代码 2026-08-11 已落地，本轮补文档 + 修跨天测试失败）
- 2026-08-11 · Round 09 · APC-T009 ObservationEvent Domain、Repository 与幂等写入完成（ObservationEvent Pydantic 契约 + Source/SyncStatus/ProcessingStatus 枚举 + SqlAlchemyObservationEventRepository event_id 幂等 upsert + EventService record/correct/soft_delete）
- 2026-08-11 · Round 08 · APC-T008 Auth API、设备注册与 seed_family 脚本完成（/api/v1/auth login/refresh/register-device/me + 鉴权依赖 + DeviceRepository + seed 脚本）
- 2026-08-11 · Round 07 · APC-T007 Auth/RBAC Domain、Repository 与 JWT 服务完成（进入 Epic E02；PBKDF2 密码哈希 + HS256 JWT 标准库实现 + RBAC 权限表）
- 2026-08-11 · Round 06 · APC-T006 审计日志服务与 @audit 装饰器完成（含 0002/0003 迁移修正 timestamptz + append trigger）
- 2026-08-11 · Round 05 · APC-T005 结构化日志 / Metrics / Tracing / 健康端点完成（含 bind_context PII 修复 + 测试隔离修复）
- 2026-08-10 · Round 04 · APC-T004 核心数据库 Schema 初版完成（28 表 ORM + 初始迁移）
- 2026-08-10 · Round 03 · APC-T003 本地基础设施 Docker Compose 与 Alembic 初始化完成
- 2026-08-10 · Round 02 · APC-T002 FastAPI 应用壳与公共基础类型完成（含 §9.1 异常类名对齐修订）
- 2026-08-02 · Round 01 · APC-T001 项目骨架初始化完成

---

## Round 12 · 2026-08-12 · APC-T012 PowerSync 适配半成品修复与外部记忆补齐

### 背景

接手时发现 T010/T011 代码已于 2026-08-11 落地并提交（`5721e4e`），但 PROJECT_STATE/DEV_LOG/CHANGELOG 只记到 T009；T012 的 contract_validator/conflict_detector 已写但未接入、无测试、未文档化，且有 mypy 错误。本轮目标：补齐外部记忆体系 + 修复静态检查 + 记录 T012 半成品状态。

### 交付

- **T012 contract_validator mypy 修复**：`server/app/sync/service/contract_validator.py` 的 `ObservationEvent` 构造中 `start_time`/`client_created_at` 来自 `_parse_dt`（返回 `datetime | None`），与必填字段类型不匹配。改为先提取局部变量 + `assert is not None` 收窄（`required=True` 缺失已抛 ValidationError，assert 是 mypy 收窄而非运行时新分支）。
- **pyproject mypy override 补 `server.tests.*`**：原 `[[tool.mypy.overrides]] module = "tests.*"` 不匹配实际测试路径 `server/tests/`（模块名 `server.tests.*`），导致 T010/T011 测试文件的 mypy 错误未被忽略。补 `server.tests.*` override（与 `tests.*` 一致 `ignore_errors = true`，符合项目渐进式收紧策略）。
- **外部记忆补齐**：PROJECT_STATE 任务表补 T010/T011 DONE + T012 IN_PROGRESS；已完成能力补 T010/T011 详情；进行中改为 T012 半成品（列缺口）；下一步改为补齐 T012 → T013。DEV_LOG 加 Round 10/11/12。CHANGELOG 加 [0.7.1]/[0.10.0]/[0.11.0]。

### 决策与权衡

- **T012 不在本轮标 DONE**：contract_validator/conflict_detector 代码虽写，但无测试、未接入 DI/main、sync-rules.yaml 仍占位、未文档化——不满足通用 DoD（测试 + 接入 + 文档）。记为 IN_PROGRESS 并列明缺口，避免"代码存在即 DONE"的虚假完成。
- **mypy override 用 `ignore_errors` 而非逐个修测试类型**：测试替身（`_FakeAuditService` 等）与生产 Protocol/具体类的类型差异是测试常见模式，逐个加 `type: ignore` 易冗余且触发 `warn_unused_ignores`。整体 ignore 与项目"渐进式收紧"（`disallow_untyped_defs = false`）一致；后续可单独收紧测试类型。

### 测试与验收

- `make lint` ✅（ruff check + format check，121 文件）；`make typecheck` ✅（mypy，116 source files no issues）。
- `pytest server/tests/`：**230 passed**（191 unit + 39 integration），与 T011 记录一致。

### 红线与边界

- 未读取/操作 `.env`；未碰 `AI-Parenting-Copilot/`；未写入工厂根 docs。
- 未改变架构边界（sync 模块为 §9 PowerSync 适配层，contract_validator 是同步契约校验，非业务逻辑）。

### 下一步

补齐 APC-T012（测试 + DI 接入 + sync-rules.yaml + 文档），然后 APC-T013 Normalization。

---

## Round 11 · 2026-08-12 · APC-T011 PG LISTEN/NOTIFY 事件总线补记

### 背景

T011 代码于 2026-08-11 落地并提交（`5721e4e`），但 DEV_LOG/CHANGELOG 未记录。本轮补记以保持外部记忆与代码一致。

### 交付（代码 2026-08-11 已落地）

- **`server/migrations/versions/0004_event_notify_trigger.py`**：`observation_event` AFTER INSERT/UPDATE/DELETE 触发 `pg_notify('events.changed', json)`，payload 含 event_id/baby_id/operation（用 `pg_notify` 而非 `NOTIFY` 语句以携带 JSON payload；原生 NOTIFY 只支持字符串）。
- **`server/app/common/event_bus.py` 增 `PgListenEventBus`**：asyncpg 独立连接 `add_listener` 订阅 `events.changed`（不与 SQLAlchemy 池混用，避免连接池语义冲突）；通知投递到 asyncio queue 供消费循环处理；at-least-once 投递，业务幂等由消费方保证。
- **`server/app/events/service/event_worker.py`**：`EventWorker`（订阅 events.changed + `recover_pending` 崩溃恢复——扫描 `processing_status=pending` 事件重新投递给 handler；NOTIFY 不持久化，错过的通知靠状态扫描补偿；handler 当前记录结构化日志，Normalization 消费方在 T013+ 接入）。
- **`server/app/settings.py` 增 `EventsSettings.pg_listen_enabled`**：dev 默认 False（用 InMemoryEventBus no-op），prod/集成测试置 True 启用 PgListenEventBus。
- **`server/app/main.py` lifespan**：`pg_listen_enabled` 时构造 PgListenEventBus + EventWorker 启动/停止；否则 InMemoryEventBus。/readyz 健康检查含 `event_bus` 状态。
- 测试：`server/tests/integration/test_event_notify.py`（真实 PG：插入/更新/删除后收到 NOTIFY、payload 解析、worker 订阅消费、recover_pending 崩溃恢复）+ `server/tests/unit/events/test_event_bus.py`。

### 决策与权衡

- **asyncpg 独立连接而非 SQLAlchemy 事件**：SQLAlchemy 的 `pg_listen` 封装在 async 池语义下较重且与 ORM session 生命周期耦合；asyncpg `add_listener` 轻量、独立连接、回调式，适合长连接监听场景。与架构 §4.1 "PG LISTEN/NOTIFY 事件总线"一致。
- **崩溃恢复用 processing_status=pending 扫描**：NOTIFY 不持久化（PG 重启或 worker 离线期间的通知会丢失），靠 `processing_status=pending` 状态扫描补偿——这是架构 §11 "at-least-once + 幂等消费 + 崩溃恢复用 processing_status" 的标准做法。消费方（Normalization）必须幂等（按 event_id 去重 + 状态推进）。
- **dev 默认关闭 pg_listen**：dev/mock 环境无需真实 PG NOTIFY，InMemoryEventBus no-op 即可；集成测试显式置 True。避免 dev 启动强依赖 PG。

### 验证

- `pytest server/tests/`：230 passed（含 test_event_notify.py 集成 + test_event_bus.py 单元）。
- 验收：本地 dev 启用 `pg_listen_enabled` 后 worker 能订阅并打印事件变更日志；崩溃恢复扫描 pending 事件可补处理。

---

## Round 10 · 2026-08-12 · APC-T010 Events API 补记 + T007 JwtService.parse 时钟不对称修复

### 背景

T010 代码于 2026-08-11 落地并提交（`5721e4e`），但 DEV_LOG/CHANGELOG 未记录；且接手时 `make test` 有 1 个失败 `test_issue_and_authenticate_token_roundtrip`（TokenExpiredError）。本轮补记 T010 + 修复 T007 遗留的时钟不对称 bug。

### 交付

#### T010 Events API（代码 2026-08-11 已落地）

- **`server/app/events/api/routes.py`**：`/api/v1/events` POST/GET/`{id}/correct`/DELETE `{id}`。POST 以 event_id 幂等（架构 §505）；correct 走 correction 链（软删除旧 + 新事件 correction_of 指向旧）；DELETE 置 is_deleted=true（不物理删除，§5.1）；GET 按 start_time DESC、默认排除软删除、支持 baby_id/family_id/event_type 过滤。
- **`server/app/di.py` 增 `EventContext`**（dataclass：EventService + AuditService 共享同一请求 session，§10.4 不可绕过，避免 T008 阶段 audit 与业务跨 session 的不一致窗口）+ `get_event_context_dep`（按请求构造，yield 后 dispose）。
- RBAC：`event:write`（POST/DELETE/correct）、`event:read`（GET），deny → ForbiddenError 403。
- 审计：mutating 操作经 `EventService` 接 `ctx.audit_service` 留痕（共享 session，同事务提交）。
- 测试：`server/tests/integration/test_events_api.py`。

#### T007 JwtService.parse 时钟不对称修复（2026-08-12）

- **问题**：`Hs256JwtService.parse` 原硬读 `datetime.now(tz=UTC)` 做过期校验，而 `issue` 用注入 Clock（AuthService 持有 `self._clock`）。测试 fixture `clock=FixedClock(2026-08-11 12:00)` 签发 token（exp=13:00），但今天真实日期 2026-08-12，`parse` 用 wall clock 校验 → 过期 → `test_issue_and_authenticate_token_roundtrip` 失败。
- **修复**：`Hs256JwtService` 构造函数加 `clock: Clock | None = None`（默认 SystemClock），`parse` 用 `self._clock.now()` 过期校验，与 `issue` 对称。Protocol `JwtService.parse` 签名不变（向后兼容）。DI 装配传 container.clock；测试 fixture `jwt_svc` 传同一 FixedClock。
- 文件：`server/app/auth/service/jwt.py`、`server/app/di.py`、`server/tests/unit/auth/test_auth_service.py`。

### 决策与权衡

- **修 JWT 时钟而非调测试 fixture 时间**：根因是 `parse` 与 `issue` 时钟来源不对称（设计缺陷），不是测试时间设置问题。改 fixture 用真实 now 会让测试依赖 wall clock（flaky）。正确修法是让 `parse` 也接受注入 Clock，测试可控、生产路径仍用 SystemClock，与项目"测试通过注入替身控制时间，不依赖系统时钟"（common/clock.py docstring）原则一致。
- **Protocol 不变**：`JwtService.parse(token) -> TokenClaims` 签名不变，只实现类构造函数加参数，向后兼容，不影响其他实现/测试。

### 验证

- 修复前：`make test` 1 failed（test_issue_and_authenticate_token_roundtrip TokenExpiredError）。
- 修复后：`make lint` ✅、`make typecheck` ✅、`pytest server/tests/` **230 passed**。
- 验收 T010：同一 family/baby 可查询事件时间线；软删除事件不出现在普通查询但审计可追溯；所有 mutating 操作有审计。

---

## Round 09 · 2026-08-11 · APC-T009 ObservationEvent Domain、Repository 与幂等写入

### 交付

- **events/domain/observation_event.py**：`ObservationEvent` Pydantic 契约（§5.1 SSOT，frozen + extra=forbid）+ `Source`(manual/voice_text/camera/sensor/ai/system)、`SyncStatus`(pending/synced)、`ProcessingStatus`(pending/normalized/projected) 三个 StrEnum + `ObservationEventRepository` Protocol（get/upsert/query/soft_delete）。
- **events/infra/repository.py**：`SqlAlchemyObservationEventRepository`（基于 AsyncSession，flush 不 commit）；`_to_orm`/`_from_orm` 集中 Pydantic↔ORM 互转；`upsert` 幂等——先按 event_id 查，已存在返回既有记录（不创建重复行、不抛 ConflictError）；`query` 默认排除软删除、按 start_time DESC；`soft_delete` 置 is_deleted=true（不物理删除）。
- **events/service/idempotency.py**：`EventService`（record/correct/soft_delete）；`record` 以 event_id 幂等键去重、`server_received_at` 由注入 Clock 填充、ULID 校验；`correct` correction 链（软删除旧事件 + 新事件 correction_of 指向旧 event_id）；mutating 方法成功后 `_commit()`（事务边界在 service；Fake 替身无 session 跳过）；可选 `audit: AuditService | None`（T009 无 API 层，T010 gateway 注入启用留痕）。
- **tests/unit/events/**：`test_observation_event.py`（21 项 Pydantic 契约：必填/枚举/confidence 边界/extra forbid/frozen/默认值）+ `test_event_service.py`（11 项用例：record/幂等/ULID 校验/correct 链/soft_delete/query，Fake 替身不依赖 DB）。
- **tests/integration/test_event_repository.py**：6 项端到端（真实 PG：upsert 写入、幂等无重复行、correction 链、软删除不物理删除、query 过滤排序、双状态字段持久化）。

### 决策与权衡

- **processing_status 枚举值以 ORM 为 SSOT**：ENGINEERING_DESIGN §5.1 文本示例写作 `raw|normalized|derived`，但 §6.2 与 ORM（T004 已迁移落地）统一为 `pending|normalized|projected`。domain 枚举严格对齐 ORM CHECK 约束 `ck_observation_event_processing_status`，避免写入被 DB 拒绝。已在 domain docstring 记录此 SSOT 取舍。
- **幂等 upsert 不更新既有记录内容**：`upsert` 对已存在 event_id 返回既有记录（不覆盖）。纠错走 correction 链（软删除旧 + 新建指向旧），而非原地覆盖——符合架构 §5.1 correction 链语义，且保留审计追溯。重复提交（客户端重试/网络重传）同一 event_id 不产生重复事件（架构铁律 8：离线记录不得丢失）。
- **event_id 由调用方提供**：客户端生成 ULID，断网记录成功即视为记录成功（架构铁律 8）。服务端据此去重，`record` 不自生成 event_id（幂等键语义）；`correct` 新事件 event_id 由服务端 `new_id()` 生成（纠错是服务端动作）。
- **server_received_at 由服务端 Clock 填充**：不接受调用方覆盖（同步契约字段，架构 §6.3，服务端权威接收时间）。`client_created_at` 由调用方提供（客户端时间）。
- **审计暂缓（与 T008 一致）**：mutating 方法接可选 `audit: AuditService | None`，T009 无 API 层故 `audit=None` 跳过留痕；T010 gateway 注入 AuditService 启用留痕（§10.4 不可绕过）。`_current_actor` 从 logger contextvars 取 user_id/device_id/system，与 `@audit` 装饰器一致。
- **未引入新基础设施**：复用 T004 的 `observation_event` 表（含双状态字段 CHECK + 索引）、T002 的 `common/ids`/`common/clock`/`common/errors`、T006 的 `AuditService`。无新迁移、无新依赖。

### 测试与验收

- 单元测试：32 项通过（Pydantic 契约 21 + EventService 用例 11）。
- 集成测试：6 项通过（真实 PG `AI_parenting_dev`，含 FK 前置建 family+baby）。
- 全量：207 passed（unit 180 + integration 27），ruff/mypy 干净。
- 验收标准达成：合法同步契约事件可写入；重复写入返回同一 event_id（幂等）；correction_of 与 is_deleted 字段保留；事件可被 API/Sync/Normalization 共用（领域模型 + 仓储协议解耦）。

### 红线与边界

- 未读取/操作 `.env` 文件（红线）；集成测试连 `AI_parenting_dev` 独立库，与兄弟项目隔离。
- 未改变架构边界（events 模块为 §3.1 M04 事件层）；枚举值差异以 ADR 级 docstring 记录，未新增 ADR（ORM 已落地为 SSOT）。
- LLM/剂量/医疗判断未涉及（T009 为纯数据层，无 LLM 调用、无规则引擎）。

---

## Round 08 · 2026-08-11 · APC-T008 Auth API、设备注册与 seed_family 脚本

### 交付

- **auth/api/routes.py**：`/api/v1/auth` login/refresh/register-device/me；`Annotated` 风格 Depends。
- **di.py**：`get_session_dep`/`get_auth_service_dep`（请求作用域，注入 UserRepo+DeviceRepo+session+单例）/`get_principal_dep`（Bearer token → Principal，缺失/非法→AuthError 401）。
- **domain/infra**：`DeviceKind` 枚举 + `DeviceRecord`/`DeviceRepository` Protocol + `SqlAlchemyDeviceRepository`。
- **auth_service**：`register_device`（RBAC device:register，deny→ForbiddenError）；mutating 方法成功后 `_commit()`（事务边界在 service；Fake 替身无 session 跳过）。
- **main.py**：注册 auth 路由。
- **scripts/seed_family.py**：幂等创建默认家庭+父母 Admin+baby。

### 决策与权衡

- **Annotated 风格 Depends**：避免 ruff B008（`Depends` 在默认参数），FastAPI 推荐写法；定义 `AuthServiceDep`/`PrincipalDep` 别名。
- **事务边界在 service**：AuthService mutating 方法成功后 `await self._commit()`（若有 session）。Fake 替身测试不传 session，跳过 commit。符合架构 §5.2"事务边界在 service"。
- **设备注册审计留痕暂缓**：register_device 的 audit 与 device 若跨 session（get_audit_service_dep 独立 session）有不一致窗口（device 已 commit 但 audit 失败）。T008 阶段 `audit=None` 不留痕，待 T009+ 统一 session 管理后接入（§10.4）。DEV_LOG 记录此简化。
- **refresh 滑动续期**：P0 用未过期 access token 换新 token（无独立 refresh token / 吊销列表）。V1+ 演进（架构 §19）。
- **测试分两类**：HTTP 流程用 `dependency_overrides` 注入内存替身（避免 TestClient event loop 与 asyncio.run 跨循环的 engine 死连接问题，test_audit 注释）；DB 写入用纯 `asyncio.run` + `reset_db`（与 test_audit 同模式，单 asyncio.run 内完成 seed+验证）。
- **seed 脚本幂等**：按 family.name + user.display_name 去重，重复执行返回相同 id；`sex` 默认 None（受 CHECK 约束 IN male/female）。

### 验证

- `make lint`/`make typecheck` ✅ 96 文件无错；`pytest server/tests/` **169 passed**（135 unit + 34 integration，新增 9 个 auth API integration）。
- 验收：API 前缀 /api/v1/auth ✅；设备注册 phone/camera/mmwave/mac ✅；FCM token 独立字段 ✅；seed 脚本创建家庭/父母/baby 幂等 ✅；login→token→protected ✅；device registration 写入 DB ✅。

### 下一步

APC-T009 — ObservationEvent Domain、Repository 与幂等写入（依赖 T004,T008；均已满足）。

---

## Round 07 · 2026-08-11 · APC-T007 Auth/RBAC Domain、Repository 与 JWT 服务

### 交付

进入 Epic E02（权限、事件、同步与派生状态）首任务。实现 auth 模块三层（domain/service/infra）+ DI 装配 + 单元/集成测试。

- **domain**（`server/app/auth/domain.py`）：`Role` StrEnum（Admin/Caregiver/Viewer/System，§19）、`Principal`（鉴权产物）、`TokenClaims`（JWT claims SSOT）、`permissions_for` 权限表（P0 Admin 完整、System 自动写入、Caregiver/Viewer 预留 V2、未列出默认 deny）、`PasswordHasher`/`JwtService`/`UserRepository` Protocol、`UserRecord`/`FamilyRecord` 结构化协议（解耦 ORM + mypy 检查）。
- **service**：
  - `password.py` — `Pbkdf2PasswordHasher`（标准库 `hashlib.pbkdf2_hmac` sha256 + 随机 salt + `hmac.compare_digest` 常量时间；存储 `pbkdf2_sha256$iter$salt_b64$digest_b64`；不引入 passlib/argon2/bcrypt）。
  - `jwt.py` — `Hs256JwtService`（标准库实现 HS256 JWT，不引入 PyJWT；防 alg=none 降级；解析失败抛 `AuthError` 子类 TokenMalformed/TokenInvalid/TokenExpired/AuthConfig；缺密钥 fail-fast）。
  - `auth_service.py` — `AuthService`（`authenticate` 登录防用户枚举、`issue_token`/`authenticate_token` 往返、`can`/`authorize` RBAC deny→ForbiddenError、`create_family`/`create_user` 密码哈希存储 + 重复 ConflictError + 可选 audit 留痕）。
- **infra**（`server/app/auth/infra/repository.py`）：`SqlAlchemyUserRepository`（AsyncSession 请求作用域，flush 不 commit，软删除过滤）。
- **settings/di**：`AuthSettings`（jwt_secret/jwt_algorithm/access_ttl_seconds/password_iterations）；`Container` 装配 `JwtService`/`PasswordHasher` 无状态单例；`parenting-env.example` 增 `PARENTING_AUTH__*`。

### 决策与权衡

- **不引入新依赖**：pyproject 未声明 PyJWT/passlib/argon2/bcrypt。JWT 用标准库 hmac/hashlib/base64/json 实现 HS256（RFC 7519/7515）；密码哈希用标准库 `hashlib.pbkdf2_hmac`。遵循最小依赖原则，社区常见做法，无外部依赖风险。
- **JWT 算法选 HS256**：文档未强制算法（只规定 claims）。HS256 对称签名适合局域网家庭场景（单一服务签发/校验，无需非对称密钥分发）；密钥来自 `Settings.auth.jwt_secret`（§8.3，gitignored）。
- **AuthError 细分子类放 auth/service/jwt.py 而非 common/errors.py**：§9.1 SSOT 只列基类，JWT 解析细分（过期/签名错/格式错）是 auth 内部关注点，网关层只看 `AuthError`→401。沿用 `ForbiddenError` 作为 `AuthError` 子类的先例。
- **UserRepository 协议返回结构化 Protocol（UserRecord/FamilyRecord）而非 object**：纯 `object` 让 `AuthService` 属性访问失去 mypy 检查；结构化 Protocol 既解耦 ORM（鸭子类型，ORM User/Family 天然满足）又保留类型安全。
- **AuthService mutating 方法接可选 audit 而非强制 @audit 装饰器**：T007 无 API 层（T008 才做 gateway），`@audit` 装饰器要求 `audit: AuditService` kwargs 且 None 抛 TypeError，会让 T007 单元测试复杂。改用 `audit: AuditService | None` 手动 append，T008 gateway 注入即启用留痕（§10.4），分层清晰。
- **测试放 `server/tests/unit/auth/` 而非 T007 涉及文件清单写的 `server/app/auth/tests/`**：项目实际约定是 `server/tests/unit/<module>/`（与现有 `unit/common/` 一致），pyproject `testpaths` 指向 `server/tests`。遵循项目实际约定。

### 验证

- `make lint`（ruff check + format check）✅；`make typecheck`（mypy）✅ 91 文件无错。
- `pytest server/tests/`：**160 passed**（135 unit + 25 integration）。
  - unit/auth：test_password 7 + test_jwt 10 + test_auth_service 22 = 39。
  - integration/test_auth：3（连 AI_parenting_dev，端到端建家建人哈希存储、authenticate 成功/失败、JWT 往返）。
- 验收对照：可创建 family/user ✅；Admin 可通过鉴权依赖获得 Principal ✅；非授权角色访问受限方法被拒 ✅；密码不得明文存储 ✅；JWT 含 user_id/family_id/role/device_id ✅；Auth service 可被 API Gateway 使用（DI 装配）✅。

### 下一步

APC-T008 — Auth API、设备注册与 seed_family 脚本（依赖 T004,T007；T007 已满足）。接入 gateway 鉴权依赖工厂、`/api/v1/auth/login`+`/refresh` 路由、设备注册、`seed_family.py` 种子脚本，并启用 mutating API 的 `@audit` 留痕。

---

## Round 06 · 2026-08-11 · APC-T006 审计日志服务与 `@audit` 装饰器

**任务**：APC-T006 — 实现不可删除审计写入服务与 mutating API 装饰器。

**完成内容**：

1. **`server/app/observability/audit.py`（AuditService）**：
   - `append()` 向 `audit_log` 追加记录；trace_id/request_id 从 logger contextvars 取，嵌入 `after` JSONB（架构 §6.1 表无 trace_id 列，SSOT 不改）。
   - 写入失败 → `UpstreamUnavailable`（503），mutating 操作不得静默成功（§10.4）。
   - 仅 append，不提供 update/delete（append-only）。
2. **`server/app/common/audit_decorator.py`（@audit 装饰器）**：
   - `@audit(action=, resource=, load_before=)` 装饰 mutating API/service 方法。
   - 两种返回约定：dict（作 after 快照）或 `AuditResult`（显式 before/after/rule_version/llm_call_id）。
   - `load_before` 异步钩子提供 before 快照；actor 从 contextvars 取（user_id → device_id → system）；资源模板 `{kwarg}` 填充；从签名取 `audit: AuditService` 参数，缺则 TypeError。
3. **迁移 `0002_timestamps_tz`（T004 修正）**：
   - 根因：0001 迁移中 18 个时间戳列用 `sa.DateTime()`（无时区），与架构 SSOT（§6.1 + models/base.py 文档"DB 列用 TIMESTAMP WITH TIME ZONE"）不一致。T006 `AuditService.append` 写 timezone-aware datetime 到 naive `audit_log.ts` 列时，asyncpg 报 "can't subtract offset-naive and offset-aware datetimes"。
   - 修复：ALTER 18 个 naive 列为 `TIMESTAMPTZ`（`USING col AT TIME ZONE 'UTC'`，原值是 UTC 不偏移）；模型同步 `DateTime(timezone=True)`。
4. **迁移 `0003_audit_append_trigger`（T004 修正）**：
   - 根因：0001 用 `REVOKE UPDATE/DELETE FROM parenting` 强制 append-only，但 `parenting` 是 `audit_log` owner，PG 中 owner 隐式持全权限，REVOKE 撤不掉——集成测试证实 UPDATE/DELETE 仍可执行（append-only 被破坏）。
   - 修复：挂 `BEFORE UPDATE/DELETE` trigger（`parenting_audit_log_append_only()`）抛异常，owner 也无法绕过（PG append-only 标准做法）。REVOKE 保留作纵深防御。
5. **测试**：
   - `test_audit_decorator.py`（9 用例，Unit：decorator 捕获 before/after）。
   - `test_audit.py`（4 用例，Integration：插入成功含 trace_id 嵌入 / UPDATE 被拒 / DELETE 被拒 / 写入失败 UpstreamUnavailable）。
   - `test_migration_apply.py` 增 `test_timestamps_are_timestamptz` + `test_audit_log_is_append_only` 增 trigger 校验。
   - 118 passed（104 → 118，+14）。

**验收**：
- `python -m pytest`：118 passed，0 failed。
- `ruff check server tests`：All checks passed。
- `python -m mypy server/app`：Success, no issues found in 51 source files。
- T006 验收标准达成：任一接入 `@audit` 的测试 API 调用后有审计记录（decorator 测试覆盖）；审计日志无法通过应用 repository 删除（trigger 层强制，集成测试覆盖）。
- **Milestone 1（APC-T001 ~ T006）全部 DONE**。

**下一步**：进入 Epic E02，APC-T007 — Auth/RBAC Domain、Repository 与 JWT 服务（依赖 T004,T006，均已满足）。

---

## Round 05 · 2026-08-11 · APC-T005 结构化日志 / Metrics / Tracing / 健康端点

**任务**：APC-T005 — 实现 structlog JSON 日志、Prometheus `/metrics`、OpenTelemetry 基础 tracing、系统健康端点。

**背景**：本轮接手时，T005 的源码（observability/logger.py / metrics.py / tracing.py、health/api.py、gateway/middleware/logging.py、main.py 装配）已在工作树中（git 未跟踪），但：
1. 文档（PROJECT_STATE/CHANGELOG/DEV_LOG）仍记 T005 为 🔄 NEXT，未记录完成。
2. 全量 `pytest` 失败 1 例：`test_validation_error_uses_envelope`（`/readyz` 返回 503 而非 200）。
3. T005 验收要求的测试（Unit：PII mask；Integration：request_id / `/metrics` Prometheus 格式）缺失。
4. `ruff check` 报 4 处（`__all__` 未排序、import 未排序、未用 import）；`mypy` 报 1 处（`add_request_logging(app: ASGIApp)` 无 `add_middleware` 属性）。

**完成内容**：

1. **修复测试隔离（`/readyz` 跨测试 503）**：
   - 根因：`test_migration_apply` 用 `asyncio.run`（独立事件循环 A）跑迁移并 `dispose_db()`，但进程级 `_engine` 缓存遗留绑定到循环 A；后续 `test_validation_error_uses_envelope` 的 TestClient（循环 B）`/readyz` → `check_db` → `get_engine()` 拿到绑定已关闭循环的 engine → `SELECT 1` 抛 "Event loop is closed" → `check_db` 捕获返回 "degraded" → 503。
   - 修复：`tests/conftest.py` `client` fixture 增加 `db_module.reset_db()`（进入与退出各一次），每个 TestClient 按当前循环重建 engine，避免跨测试死连接。
2. **修复 `bind_context` PII 脱敏失效**：
   - 根因：`bind_context` 原实现 `{k: mask_pii(v) for k, v in kwargs.items()}`——对值逐个跑 `mask_pii`，字符串不知 key 名，命中 `_SENSITIVE_KEYS`（如 `raw_input`）的整体脱敏失效。`bind_context(raw_input="宝宝发烧 38.5")` 会把非正则命中的 PII（"宝宝发烧 38.5"）原样写入日志上下文。
   - 修复：改为 `mask_pii(dict(kwargs))`，走 dict 分支，命中敏感 key 整体替换 `***`。新增 `test_bind_context_masks_pii` 验证。
3. **修复 lint / type**：
   - `ruff --fix`：`__all__` 排序、import 排序、移除未用 `dispose_db` import。
   - `add_request_logging(app: ASGIApp)` → `app: Starlette`（`from starlette.applications import Starlette`），FastAPI 兼容（FastAPI 是 Starlette 子类），`add_middleware` 属性可见，mypy 通过。
4. **补齐 T005 验收测试**：
   - `server/tests/unit/common/test_pii_mask.py`（7 用例）：敏感 key 整体 `***`、手机号/邮箱/身份证正则、媒体路径文件名脱敏、dict/list/tuple 递归、非 str 原样、bind_context 脱敏、clear_context 重置。
   - `server/tests/integration/test_observability.py`（6 用例）：X-Request-Id 回写、X-Trace-Id 入站透传、X-Trace-Id 无则生成、`/metrics` Prometheus 格式含核心指标名、`metrics_response_body` helper、`/readyz` 200 + checks。
5. **文档同步**：PROJECT_STATE（T005 ✅ DONE、T006 🔄 NEXT、已完成能力增补 T005 段、进行中/下一步更新）、CHANGELOG [0.5.0]、DEV_LOG Round 05。

**验收**：
- `python -m pytest`：104 passed（91 → 104，+13），0 failed。
- `ruff check server tests`：All checks passed。
- `python -m mypy server/app`：Success, no issues found in 49 source files。
- T005 验收标准达成：每次 HTTP 请求有结构化日志（middleware + contextvars）；`/healthz` 与 `/metrics` 可访问；Unit PII mask + Integration request_id / `/metrics` Prometheus 格式测试齐备。

**下一步**：APC-T006 — 审计日志服务与 `@audit` 装饰器（依赖 T004,T005，均已满足）。

---

## Round 04 · 2026-08-10 · APC-T004 核心数据库 Schema 初版

**任务**：APC-T004 — 实现核心表结构 migration，覆盖 P0 与未来预留实体（28 表 ORM + 初始迁移）。

**完成内容**：

1. **ORM 模型 `server/app/models/`**（按域分文件，共享 `Base`）：
   - `base.py`：`Base`（DeclarativeBase）+ `ULIDPrimaryKey`（String(26)）+ `TimestampMixin`（created_at/updated_at timezone-aware UTC）+ `SoftDeleteMixin`（is_deleted）。
   - `core.py`：family/user/device/baby（§6.1；device.kind 枚举 phone/camera/mmwave/mac，baby.sex 枚举，allergies jsonb，vaccine_region 默认 CN）。
   - `events.py`：ObservationEvent（§5.1 数据契约 SSOT；idx(baby_id,event_type,start_time DESC)；双状态 sync_status(pending|synced)+processing_status(pending|normalized|projected)；correction_of 自引用；source 枚举）。
   - `logs.py`：13 个 *_log（feeding/diaper/sleep/temperature/supplement/vaccine/medication/symptom/jaundice/milestone/growth/solid_food/media_asset），各含 event_id FK 溯源；feeding_log 含 P0 结构化列（amount_ml/feeding_type/started_at/ended_at），media_asset 存路径不存二进制。
   - `derived.py`：derived_baby_state（baby_id PK + snapshot jsonb）、alert（多级阈值 gray/blue/yellow/orange/red + ack 状态机）、alert_delivery（送达审计）、sleep_session（状态机）、sensor_event/camera_event（证据溯源，不可删除）。
   - `rules.py`：family_knowledge（M2 家庭偏好，family_id+key UNIQUE）、evidence_policy（规则版本化，type+region+version UNIQUE）、audit_log（append-only，不继承软删除）、sync_state（client_id PK）。
2. **初始迁移 `server/migrations/versions/9dc5086c5ca6_initial_schema.py`**（autogenerate + 手补）：
   - 28 张表 + 索引 + 约束（CHECK/UNIQUE/FK）autogenerate 生成。
   - 手补：全表 `updated_at` trigger（`parenting_set_updated_at()` 函数 + 26 表 trigger，表名加双引号规避 `user` 保留字）；`audit_log` REVOKE UPDATE/DELETE FROM PUBLIC/parenting（append-only，§22.2）。
   - `server/migrations/script.py.mako`（alembic 官方 async 模板）。
3. **env.py 接入**：`target_metadata = Base.metadata`，autogenerate 与 upgrade 对齐 ORM。
4. **测试**：
   - `test_models.py`（unit，20+ 用例）：28 表注册、ULID PK String(26)、ObservationEvent §5.1 字段与枚举约束、§6.1 索引、device.kind/baby.sex/alert.level CHECK、evidence_policy/family_knowledge UNIQUE、audit_log append-only（无 is_deleted）、sync_state/derived_baby_state PK、各 *_log event_id FK、feeding_log P0 列、sensor_event/camera_event/alert_delivery 不可删除、media_asset 存路径、timestamped 表 timezone-aware、软删除表 is_deleted。
   - `test_migration_apply.py`（integration，4 用例）：迁移应用后 28 表存在、26 个 updated_at trigger 挂载、audit_log 对 parenting 角色无 UPDATE/DELETE（append-only）、alembic_version 记录初始版本。

**验证**：

- `make lint`（ruff）：All checks passed，70 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 68 source files。
- `make test` + integration（pytest）：91 passed。
- 实跑迁移：`alembic upgrade head` 在 `AI_parenting_dev` 库成功应用；验证 29 表（28 业务 + alembic_version）、26 trigger、audit_log REVOKE 生效（parenting 角色仅 INSERT/SELECT/TRUNCATE/REFERENCES/TRIGGER，无 UPDATE/DELETE）。

**遵循的边界**：

- 严格遵守文档优先级；表结构对齐 ENGINEERING_DESIGN §6.1/§6.2 与 §5.1，架构边界/模块职责未改动。
- ULID 统一 PK、软删除 partial index、updated_at trigger、audit_log append-only REVOKE 均按 §6.2/§22.2 实现。
- 未读取/操作 `.env` 文件（红线）；迁移连 `AI_parenting_dev` 独立库，与兄弟项目隔离。

**源码与文档不一致（已记录，按 §6.2 实现）**：

- **§5.1 vs §6.2 processing_status（分类 C）**：§5.1 ObservationEvent 契约未列 `processing_status`，§6.2 列出 `processing_status(pending|normalized|projected)`。按 §6.2 实现（§5.1 为领域层最小集，§6.2 为存储层状态机扩展，不冲突）。
- **各 *_log 最小结构（设计决策）**：§6.1 只说"各含 event_id FK 溯源"未列具体字段。T004 各 *_log（除 feeding_log）用最小结构（event_id + baby_id + payload jsonb），结构化列留待各领域任务细化；feeding_log 含 P0 端到端结构化列。

**下一步**：APC-T005 — 结构化日志 / Metrics / Tracing / 健康端点（依赖 T002，已满足）。

**模型**：Claude Opus 4.8（1M context）

---

## Round 03 · 2026-08-10 · APC-T003 本地基础设施 Docker Compose 与 Alembic 初始化

**任务**：APC-T003 — 提供本地开发基础设施（PostgreSQL/Mosquitto/PowerSync）并初始化 SQLAlchemy async 与 Alembic。

**完成内容**：

1. **Docker Compose 栈 `deploy/docker-compose.yml`**：
   - PostgreSQL 15-alpine（权威源，架构 §7），healthcheck `pg_isready`，卷 `parenting-pg-data`，TZ=UTC（与 clock.py 对齐）。
   - Eclipse Mosquitto 2（消息总线，架构 §13），监听 1883，卷持久化，配置挂载 `deploy/mosquitto/mosquitto.conf`。
   - PowerSync Service（`journeyapps/powersync-service`，架构 §9 复用官方不自研），depends_on postgres healthy，配置挂载 `config/powersync/`。
   - 变量从 `deploy/.env` 读取，`${VAR:-default}` 缺省值确保无 `.env` 亦可启动。
2. **配套配置**：
   - `deploy/mosquitto/mosquitto.conf`：本地 dev 允许匿名、监听 1883、持久化、日志（prod 通过 _infra 注入 ACL+TLS）。
   - `config/powersync/config.yaml`：实例名、sync rules 路径、API 8080。
   - `config/powersync/sync-rules.yaml`：空 bucket 占位，待 APC-T004 Schema 定型后按 §9.2 填充分桶规则。
3. **SQLAlchemy async `server/app/db.py`**：进程级 async engine（`create_async_engine`，pool_pre_ping、pool_size/max_overflow 来自 Settings）+ async_sessionmaker（expire_on_commit=False）；惰性单例（`get_engine`/`get_session_factory`）；FastAPI 依赖 `get_session`（按请求 yield session）；`reset_db`/`dispose_db`（测试 teardown / 应用 shutdown）。写入统一走 Repository（架构 §4），本模块不含业务逻辑。
4. **Alembic 框架**：
   - `server/migrations/env.py`：async env，URL 从 `Settings.database` 注入（`config.set_main_option`）不硬编码；`run_migrations_offline`（--sql 生成脚本）+ `run_migrations_online`（async engine 执行）；`target_metadata=None` 占位，待 APC-T004 填充 ORM Base。
   - `alembic.ini`：`script_location=server/migrations`，日志配置，URL 占位由 env.py 覆盖。
5. **Makefile 增补**：`infra-logs`（follow 日志）、`infra-reset`（down -v 清卷重建）、`db-current`（当前版本）、`db-history`（迁移历史）、`db-revision m="..."`（autogenerate）。
6. **测试**：
   - `server/tests/unit/common/test_db.py`：engine/session factory 惰性创建与单例、reset 清空、URL 来自 Settings、pool_pre_ping、dispose 幂等（6 用例）。
   - `server/tests/unit/common/test_alembic_config.py`：alembic.ini 可解析且 script_location 正确、env.py AST 语法与关键符号、versions 目录、compose 三服务声明、mosquitto/powersync 配置存在（6 用例，不连 DB）。

**验证**：

- `make lint`（ruff check + format --check）：All checks passed，60 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 59 source files。
- `make test`（pytest）：51 passed（T002 的 39 + T003 的 12）。
- 实启动校验：`docker compose config --services` → postgres/mosquitto/powersync 三服务声明正确；`alembic current` 可连 PG（成功连到本地 127.0.0.1:5432/parenting）；`alembic upgrade head --sql` 离线 SQL 生成正常（alembic 框架工作）。

**遵循的边界**：

- 严格遵守文档优先级；架构边界、模块职责、调用链未改动。
- 复用社区成熟实现（PostgreSQL/Mosquitto/PowerSync 官方镜像、SQLAlchemy async、Alembic），不自研同步。
- 未读取/操作 `.env` 文件（红线）；compose 缺省值已使栈无需 `.env` 可启动。
- Bootstrap 顺序对齐 §14.6（compose → alembic upgrade head → seed → FastAPI + workers）。

**源码与文档/环境不一致（已解决）**：

- **本地 PG 库冲突（分类 E，2026-08-10 裁决执行）**：本地 `127.0.0.1:5432/parenting` 库曾被兄弟项目 `projects/AI-Parenting-Copilot/` 初始化（29 表 + `alembic_version=0002_event_notify_trigger`）。老板裁决本目录用独立库名 `AI_parenting_dev`，已执行：settings 默认 URL 改为 `…/AI_parenting_dev`、compose `POSTGRES_DB`/`POWERSYNC_DB_NAME` 默认值同步；已建 `AI_parenting_dev` 库，`alembic upgrade head` 干净通过（仅 `alembic_version` 表），与兄弟项目 `parenting` 库完全隔离。
- **`.env.example` harness 拦截（部分解决）**：老板已授权在 `projects/AI-Parenting/` 目录内操作 `.env.example`，但 harness 对 `.env*` 文件名硬拦截（Write/Bash mv 均被拒，无法绕过）。已提供等价样例 `deploy/compose-env.example`（Compose 变量）与 `parenting-env.example`（应用层 `PARENTING_*` 片段），请老板手动 `cp`/追加到 `.env.example`。compose 缺省值已使栈无需 `.env` 可启动，不阻塞功能。

**下一步**：APC-T004 — 核心数据库 Schema 初版（依赖 T003，已满足；填充 ORM Base + 首个迁移 + PowerSync sync rules）。

**模型**：Claude Opus 4.8（1M context）

---

## Round 02 · 2026-08-10 · APC-T002 FastAPI 应用壳与公共基础类型

**任务**：APC-T002 — 实现 FastAPI 应用壳、Settings、DI 与公共基础类型

**完成内容**：

1. **公共基础类型 `server/app/common/`**：
   - `ids.py`：ULID 生成（`new_id`/`is_valid_ulid`/`parse_ulid`），26 字符 Crockford base32，时间有序，复用社区库 `python-ulid`。
   - `clock.py`：timezone-aware UTC 时钟（`Clock` Protocol + `SystemClock` + `ensure_aware`），`@runtime_checkable`，测试可注入替身。
   - `errors.py`：领域异常层次（`ParentingError` 基类 + `ValidationError`/`AuthError`/`ForbiddenError`/`NotFoundError`/`ConflictError`/`RuleViolation`/`DoseInterceptError`/`UpstreamUnavailable`/`UpstreamTimeout`，对齐 ENGINEERING_DESIGN §9.1）+ `ErrorEnvelope{code,message,evidence,trace_id}`，领域层不感知 HTTP，`http_status`/`code` 类属性供网关映射。
   - `repository.py`：`Repository[T]` Protocol（`get`/`upsert`/`query`），`@runtime_checkable`，PEP 544。
   - `event_bus.py`：PG LISTEN/NOTIFY 协议（`EventBus`）+ `InMemoryEventBus` 占位（dev/mock + 单测用，经 JSON 序列化模拟 NOTIFY 边界）。
2. **配置 `server/app/settings.py`**：pydantic-settings，`env_prefix="PARENTING_"` + `env_nested_delimiter="__"`，分层加载（`.env` + `_infra/.env` + 环境变量），聚合 `Database/Mqtt/Http/Models/Privacy/Notification/Observability` 子配置，`env` 校验（dev/staging/prod），`is_dev`/`is_prod` 属性，`lru_cache` 单例。
3. **依赖装配 `server/app/di.py`**：进程级 `Container`（settings/clock/event_bus + `override`/`get` 扩展点）+ 惰性单例（`get_container`/`set_container`/`reset_container`）+ FastAPI `Depends` 工厂（`get_settings_dep`/`get_clock_dep`/`get_event_bus_dep`，从 `app.state.container` 取用）。
4. **网关 `server/app/gateway/exception_handlers.py`**：全局异常处理器，领域异常按 `http_status`/`code` 映射，`RequestValidationError`→422、`StarletteHTTPException`→原状态、`Exception`→500 兜底，全部归一为 `ErrorEnvelope`，`trace_id` 贯穿链路，`register_exception_handlers(app)` 注册。
5. **应用壳 `server/app/main.py`**：`create_app(settings)` 工厂 + 模块级 `app` 单例（供 `uvicorn server.app.main:app` 启动）；lifespan（startup 装配 Container、启动 EventBus、调度已注册 worker；shutdown 取消 worker、停止 EventBus）；`/healthz` + `/readyz` 端点；`register_worker`/`clear_workers` worker 注册接口预留（APC-T002 不注册业务 worker）；`_configure_logging` 按 `observability.log_level` 配置。
6. **测试**：
   - `server/tests/conftest.py`：隔离夹具（`_isolate_env` autouse 清 PARENTING_* + 重置单例；`settings`/`container`/`client` 夹具）。
   - `server/tests/unit/common/`：`test_ids.py`（ULID 格式/有序/唯一/校验/解析）、`test_clock.py`（UTC aware/ensure_aware）、`test_errors.py`（信封字段/trace_id 生成/http_status 映射/命名空间）、`test_repository.py`（Protocol 满足）、`test_event_bus.py`（投递/通道隔离/JSON 边界/start-stop/Protocol）、`test_di.py`（装配/override）、`test_settings.py`（默认 dev/前缀+嵌套覆盖/非法 env 拒绝/大小写/CORS/observability）。
   - `server/tests/integration/test_healthz.py`：`/healthz` 200、`/readyz` 200、`/openapi.json` 可访问、`/docs` 可访问、404 统一信封、dev 无 DB 启动。

**验证**：

- `make lint`（ruff check + format --check）：All checks passed，52 files already formatted。
- `make typecheck`（mypy）：Success: no issues found in 52 source files。
- `make test`（pytest）：37 passed。
- 实启动验证：`uvicorn server.app.main:app --port 8199` 启动成功，`GET /healthz` → 200 `{"status":"ok","env":"dev","version":"0.1.0","checks":{"event_bus":"ok"}}`；`GET /openapi.json` → title/version/paths；`GET /nope` → 404 统一信封 `{code,message,evidence,trace_id}`。

**遵循的边界**：

- 严格遵守文档优先级（P0>P1>P2>P3>P4>P5>P6）；架构边界、模块职责、调用链未改动。
- 复用社区成熟实现（python-ulid、pydantic-settings、FastAPI lifespan），不重复造轮子。
- 未读取/操作 `.env` 文件（红线）；`.env.example` 已对齐 `PARENTING_` + `__`，无需修改。
- 未配置 DB 时 dev/mock 模式可启动并清晰提示（APC-T002 验收标准）。

**源码与文档不一致（已解决）**：

- `ENGINEERING_DESIGN §9.1` 异常类名（`ParentingError`/`RuleViolation`/`DoseInterceptError`/`UpstreamTimeout`/`UpstreamUnavailable`）与 APC-T002 初版实现（`DomainError`/`RuleViolationError`/`InfrastructureError`）命名不同，曾记为分类 C 待裁决。**2026-08-10 老板裁决"类名要与 ENGINEERING_DESIGN 对齐"，已重命名并对齐 http_status**（见下方"§9.1 异常类名对齐修订"）。

**§9.1 异常类名对齐修订（2026-08-10，应老板裁决执行）**：

- `DomainError` → `ParentingError`（基类 500）；`ValidationError` http_status 422→400；`UnauthorizedError` → `AuthError`（401），`ForbiddenError` 改为 `AuthError` 子类（403）；`RuleViolationError` → `RuleViolation`（422），新增 `DoseInterceptError(RuleViolation)`（422）；`InfrastructureError` → 拆为 `UpstreamUnavailable`（503）+ `UpstreamTimeout`（504）。
- 网关 `domain_error_handler` → `parenting_error_handler`。
- 测试 `test_errors.py` 同步对齐，新增 `test_forbidden_error_is_auth_error_subclass`、`test_dose_intercept_is_rule_violation_subclass`。
- 验证：`make lint` 通过、`make typecheck` 通过（55 files）、`make test` 39 passed。
- 边界：仅重命名与 http_status 对齐，未改架构/模块职责/调用链；统一信封不变。

**下一步**：APC-T003 — 本地基础设施 Docker Compose 与 Alembic 初始化（依赖 T002，已满足）。

**模型**：Claude Opus 4.8（1M context）

---

## Round 01 · 2026-08-02 · APC-T001 项目骨架初始化

**任务**：APC-T001 — 初始化项目目录与工程元数据

**完成内容**：

1. **目录骨架**：`server/app/` 下 21 个领域子模块、`server/migrations/`、`server/scripts/`、`server/tests/`（unit/integration/golden/security/e2e）、`android/`、`firmware/esp32c6/`、`config/`、`deploy/`、`tests/`、`runtime/` 已就位（前期已建）。
2. **工程元数据**：
   - `pyproject.toml`：Python 3.11+，FastAPI/Pydantic v2/SQLAlchemy 2.0 async/asyncpg/Alembic/aiomqtt/APScheduler/structlog/prometheus/opentelemetry/httpx 等依赖；ruff（line-length 100，E/F/W/I/UP/B/SIM/RUF）、mypy（渐进式）、pytest（asyncio auto + markers）配置。
   - `Makefile`：lint/format/typecheck/test/test-all/test-integration/security-test/golden/rules-validate/infra-up/infra-down/db-migrate/db-seed/run-dev/run-worker/install/docs-check/governance-check。
   - `.env.example`：PARENTING_ 前缀，分层加载（defaults→config→runtime→.env→env→CLI），无真实密钥。
3. **本次新增（APC-T001 收尾）**：
   - `.gitignore`：runtime/、.env、密钥（*.pem/*.key/fcm-service-account.json）、Python 缓存、.venv、Android build/apk/aab/keystore、固件 .pio、媒体文件忽略；保留 .gitkeep 与 tests/fixtures。
   - `README.md`：项目定位、SSOT 文档表、技术栈、快速开始、命令、目录结构、边界说明。
   - `docs/PROJECT_STATE.md`：当前状态 SSOT + 任务状态索引（供 docs-check grep）。
   - `docs/DEV_LOG.md`（本文件）、`docs/CHANGELOG.md`。
   - `docs/ADR/ADR-001-project-bootstrap.md`：骨架决策记录。
   - `server/` 全包占位 `__init__.py`（server、server/app、各领域子包、migrations、migrations/versions、scripts、tests 及各测试子目录），仅文件头注释，无业务代码。
   - `runtime/.gitkeep`：确保 runtime/ 入库但内容被忽略。

**验证**：

- `make lint`：ruff check + format --check 对空 `__init__.py` 不报错 → 通过。
- `make docs-check`：占位提示 + PROJECT_STATE 任务索引 grep → 通过。

**遵循的边界**：

- 不碰 `projects/AI-Parenting-Copilot/`。
- 不写工厂根 `docs/DEV_LOG.md` / `CHANGELOG.md` / `PROJECT_STATE.md`。
- 不复制工厂 `_infra/` 实现，只预留适配层引用点。
- 不修改 `docs/SPEC.md` 或其他 ADR。

**下一步**：APC-T002 — FastAPI 应用壳、Settings、DI 与公共基础类型。

**模型**：Claude Opus 4.8（1M context）
