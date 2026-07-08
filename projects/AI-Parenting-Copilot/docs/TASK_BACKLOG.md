<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-09 05:55:00
-->

# TASK_BACKLOG.md

> 项目：AI Parenting Copilot
> 项目根目录：`projects/AI-Parenting-Copilot/`（仓库实际目录，大小写固定）
> 主要实施依据：`docs/ENGINEERING_DESIGN.md`
> 架构事实来源：`docs/ARCHITECTURE_FINAL.md`
> 工厂能力背景：工厂根目录 `../../../PROJECT_DOSSIER_V5.md`（不要使用项目内旧拷贝）
> 状态：APC-T001 DONE；APC-T002 DONE；APC-T003 BLOCKED；APC-T004 BLOCKED；APC-T005 DONE；APC-T006 BLOCKED；APC-T007 BLOCKED；APC-T008 BLOCKED；APC-T009 BLOCKED；APC-T010 BLOCKED；APC-T018 BLOCKED；APC-T020 BLOCKED；APC-T021 BLOCKED；APC-T022 BLOCKED；APC-T023 BLOCKED；APC-T024 DONE；APC-T025 DONE；APC-T026 BLOCKED；APC-T027 BLOCKED；APC-T028 BLOCKED；APC-T029 BLOCKED；APC-T030 BLOCKED；APC-T031 BLOCKED；APC-T032 BLOCKED；APC-T033 BLOCKED。供 Claude Code / Codex 等 AI Agent 直接逐任务执行。

---

## 0. Agent 执行铁律

1. 禁止改变架构边界；如必须调整，先新增 ADR。
2. Factory-first：优先复用工厂 `_infra/`、Smart Proxy、Privacy、Local RAG、governance 能力，不复制实现。
3. LLM 调用只能经 `model_gateway`。
4. 云端出站只能经 `privacy` 脱敏。
5. 剂量、阈值、医疗判断只能由 `rule_engine` 产出。
6. LLM/Copilot 输出中的 `mg/ml/滴` 等剂量数字必须经 `dose_interceptor` 拦截。
7. 所有 mutating 操作必须写审计日志。
8. 离线记录不得丢失；Android 本地写入成功即视为记录成功。
9. 红/橙告警必须多通道送达，红色告警必须具备本地兜底。
10. 每个任务完成后更新相关文档：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、必要时更新 `docs/PROJECT_STATE.md` / ADR。

---

## 1. 通用 Definition of Done

除非任务明确说明不适用，每个 Task 的 DoD 均包含：

- 功能完成，并符合 `ENGINEERING_DESIGN.md` 与 `ARCHITECTURE_FINAL.md`。
- 单元测试通过。
- 集成测试通过；如不适用，需在提交说明中注明原因。
- 静态检查通过：Python `ruff` / `mypy`；Android `lint` / unit test；Firmware `pio test/build` 如适用。
- 不引入未批准的新基础设施。
- 不绕过 Rule Engine / Model Gateway / Privacy Gateway / Notification Orchestrator。
- Mutating 操作已接入审计。
- 文档更新完成。
- 验收标准全部满足。

---

## 2. Epic / Capability / Story 总览

### Epic E01 — 项目地基与运行治理

| Capability | Story | Tasks |
|---|---|---|
| C01 项目骨架与配置 | S01 初始化可运行工程骨架 | APC-T001, APC-T002 |
| C02 本地基础设施与数据库迁移 | S02 启动 PostgreSQL / Mosquitto / PowerSync 并建立 Schema | APC-T003, APC-T004 |
| C03 可观测性与审计 | S03 建立日志、指标、追踪、不可删除审计 | APC-T005, APC-T006 |

### Epic E02 — 权限、事件、同步与派生状态

| Capability | Story | Tasks |
|---|---|---|
| C04 Auth/RBAC | S04 家庭账号、角色、设备注册 | APC-T007, APC-T008 |
| C05 ObservationEvent 与 Event Store | S05 统一事件写入、幂等、纠错、软删除 | APC-T009, APC-T010 |
| C06 同步与事件总线 | S06 PowerSync 写入契约、PG LISTEN/NOTIFY | APC-T011, APC-T012 |
| C07 Normalization | S07 多源输入归一化为领域派生表 | APC-T013, APC-T014 |
| C08 Baby State Engine | S08 幂等增量派生 DerivedBabyState | APC-T015, APC-T016, APC-T017 |

### Epic E03 — Rule Engine、AI 编排与安全输出

| Capability | Story | Tasks |
|---|---|---|
| C09 Rule Engine Kernel | S09 规则加载、注册、EvidencePolicy 版本化 | APC-T018, APC-T019 |
| C10 规则域 | S10 用药、分诊、阈值、疫苗、生长规则 | APC-T020, APC-T021, APC-T022, APC-T023 |
| C11 Model / Privacy / Memory 适配 | S11 复用工厂模型、隐私、Local RAG 能力 | APC-T024, APC-T025, APC-T026 |
| C12 Orchestrator & Copilots | S12 意图路由、上下文注入、Dose Interceptor、P0 Copilots | APC-T027, APC-T028, APC-T029, APC-T030 |

### Epic E04 — 告警、通知、健康与调度

| Capability | Story | Tasks |
|---|---|---|
| C13 Alert Store/API | S13 告警查询、确认、反馈、审计 | APC-T031 |
| C14 Notification Orchestrator | S14 多通道扇出、送达凭证、升级状态机 | APC-T032, APC-T033, APC-T034 |
| C15 Health Monitor & Scheduler | S15 设备健康、晨报、提醒、灰色告警 | APC-T035, APC-T036 |

### Epic E05 — 摄像头、mmWave、媒体、导出与备份

| Capability | Story | Tasks |
|---|---|---|
| C16 Sleep Session & Camera | S16 睡眠会话、ROI、抓帧、影子模式 | APC-T037, APC-T038, APC-T039 |
| C17 mmWave & Firmware | S17 MQTT 雷达接入与 ESP32C6 固件 | APC-T040, APC-T041 |
| C18 Media / Export / Backup | S18 加密媒体、MD/PDF 导出、NAS 备份 | APC-T042, APC-T043, APC-T044 |

### Epic E06 — Android 应用

| Capability | Story | Tasks |
|---|---|---|
| C19 Android 基础与同步 | S19 RN Android-only 壳、Auth、PowerSync、离线写入 | APC-T045, APC-T046, APC-T047 |
| C20 Android 核心页面 | S20 Quick Record、Today、Timeline、Alert Center | APC-T048, APC-T049, APC-T050, APC-T051 |
| C21 Android 告警与睡眠会话 | S21 FCM/Notifee/FullScreenIntent、Sleep Session UI | APC-T052, APC-T053 |

### Epic E07 — 端到端验证、部署与硬化

| Capability | Story | Tasks |
|---|---|---|
| C22 DevOps & Fixtures | S22 启动脚本、Mock、Seed、治理命令 | APC-T054, APC-T055 |
| C23 E2E / Security / Soak | S23 MVP E2E、告警 E2E、安全回归、影子/稳定性验证 | APC-T056, APC-T057, APC-T058, APC-T059 |

---

# 3. Task 明细

---

## Epic E01 — 项目地基与运行治理

---

### APC-T001 — 初始化项目目录与工程元数据

- **所属 Epic**：E01 项目地基与运行治理
- **所属 Capability**：C01 项目骨架与配置
- **所属 Story**：S01 初始化可运行工程骨架
- **状态**：DONE
- **目标**：创建项目推荐目录结构、基础配置文件、文档占位与 Makefile，使项目具备可开发入口。
- **前置依赖**：无
- **输入**：`ENGINEERING_DESIGN.md` §3、§14；`ARCHITECTURE_FINAL.md` §27；工厂根目录 `../../../PROJECT_DOSSIER_V5.md` §13
- **输出**：完整项目骨架、基础文档、Makefile、`.env.example`
- **涉及模块**：project root、docs、config、deploy、server、android、firmware
- **涉及文件**：
  - 新建：`README.md`, `Makefile`, `pyproject.toml`, `.env.example`, `.gitignore`
  - 新建：`docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `docs/CHANGELOG.md`, `docs/HANDOFF.md`, `docs/ADR/ADR-001-project-bootstrap.md`
  - 新建：`server/app/__init__.py`, `android/`, `firmware/esp32c6/`, `config/`, `deploy/`, `runtime/.gitkeep`
- **实现要求**：
  - Python 版本锁定 3.11+。
  - `runtime/`、`.env`、真实密钥、媒体、日志必须 gitignored。
  - Makefile 至少提供：`test`, `lint`, `typecheck`, `docs-check`, `governance-check`, `run-dev`。
  - 不复制工厂 `_infra` 实现，只通过适配层引用。
- **测试要求**：
  - 执行 `make lint` 不应因空项目失败。
  - 执行 `make docs-check` 可运行；若治理脚本尚未接入，提供明确占位命令。
- **验收标准**：
  - 项目结构与工程设计推荐结构一致。
  - 新 Agent 可通过 `README.md` 和 `docs/HANDOFF.md` 理解入口。
  - `.env.example` 不包含真实密钥。
- **Definition of Done (DoD)**：满足通用 DoD；项目骨架可被后续任务直接使用。

---

### APC-T002 — 实现 FastAPI 应用壳、Settings、DI 与公共基础类型

- **所属 Epic**：E01
- **所属 Capability**：C01
- **所属 Story**：S01
- **目标**：实现服务端应用入口、配置加载、依赖装配、公共错误、ID、时钟、Repository Protocol。
- **状态**：DONE
- **前置依赖**：APC-T001
- **输入**：`ENGINEERING_DESIGN.md` §1.2、§3、§5、§8、§9
- **输出**：可启动的 FastAPI 应用壳与公共基础模块
- **涉及模块**：server/app/main.py, settings, di, common, gateway
- **涉及文件**：
  - 新建：`server/app/main.py`, `server/app/settings.py`, `server/app/di.py`
  - 新建：`server/app/common/errors.py`, `ids.py`, `clock.py`, `repository.py`, `event_bus.py`
  - 新建：`server/app/gateway/exception_handlers.py`
  - 修改：`pyproject.toml`, `.env.example`
- **实现要求**：
  - `settings.py` 使用 `pydantic-settings`，支持 `PARENTING_` 前缀与 `__` 嵌套。
  - 全局异常格式：`{code,message,evidence,trace_id}`。
  - ID 使用 ULID。
  - 时间统一 timezone-aware。
  - FastAPI startup 预留 worker 注册接口，但本任务不实现业务 worker。
- **测试要求**：
  - Unit：settings 环境变量覆盖、ULID 格式、异常映射。
  - Integration：`GET /healthz` 返回 200。
- **验收标准**：
  - `uvicorn server.app.main:app` 可启动。
  - OpenAPI 可访问。
  - 未配置 DB 时应用能以 dev/mock 模式启动并清晰提示。
- **DoD**：满足通用 DoD；服务端基础壳可被 Auth/Event 等后续模块接入。

---

### APC-T003 — 本地基础设施 Docker Compose 与 Alembic 初始化

- **所属 Epic**：E01
- **所属 Capability**：C02 本地基础设施与数据库迁移
- **所属 Story**：S02 启动 PostgreSQL / Mosquitto / PowerSync 并建立 Schema
- **目标**：提供本地开发基础设施：PostgreSQL、Mosquitto、PowerSync，并初始化 SQLAlchemy async 与 Alembic。
- **状态**：BLOCKED（代码/配置/静态验证完成；当前沙盒无 Docker CLI，无法完成容器健康验收）
- **前置依赖**：APC-T001, APC-T002
- **输入**：`ENGINEERING_DESIGN.md` §1.3、§4、§6、§14
- **输出**：可启动 DB/MQTT/PowerSync 栈与迁移框架
- **涉及模块**：deploy, server DB infra
- **涉及文件**：
  - 新建：`deploy/docker-compose.yml`, `deploy/.env.example`
  - 新建：`server/app/db.py`, `server/migrations/env.py`, `server/migrations/versions/.gitkeep`
  - 修改：`Makefile`, `.env.example`
- **实现要求**：
  - PostgreSQL 15+。
  - Mosquitto 2.x 暴露 1883。
  - PowerSync 使用官方镜像，不自研同步。
  - SQLAlchemy 2.0 async + asyncpg。
  - Makefile 提供 `infra-up`, `infra-down`, `db-migrate`。
- **测试要求**：
  - Integration：testcontainers 或 compose 环境下连接 PG。
  - Smoke：Mosquitto 端口可连接。
- **验收标准**：
  - `make infra-up` 后 PG/MQTT/PowerSync 容器健康。
  - `alembic upgrade head` 可执行。
- **DoD**：满足通用 DoD；基础设施可支撑数据库任务开发。

---

### APC-T004 — 创建核心数据库 Schema 初版

- **所属 Epic**：E01
- **所属 Capability**：C02
- **所属 Story**：S02
- **目标**：实现核心表结构 migration，覆盖 P0 与未来预留实体。
- **状态**：BLOCKED（metadata/migration/static/offline SQL 已完成；空库 `alembic upgrade head` 需 PostgreSQL 验收）
- **前置依赖**：APC-T003
- **输入**：`ENGINEERING_DESIGN.md` §6；`ARCHITECTURE_FINAL.md` §6、§7
- **输出**：Alembic migration、SQLAlchemy metadata/models 初版
- **涉及模块**：auth, events, state_engine, rule_engine, notification, media, observability
- **涉及文件**：
  - 新建：`server/app/models.py` 或 `server/app/*/infra/models.py`
  - 新建：`server/migrations/versions/0001_initial_schema.py`
  - 修改：`server/app/db.py`
- **实现要求**：
  - 表至少包含：`family`, `user`, `device`, `baby`, `observation_event`, 领域派生表、`derived_baby_state`, `alert`, `alert_delivery`, `sleep_session`, `family_knowledge`, `evidence_policy`, `sensor_event`, `camera_event`, `media_asset`, `audit_log`, `sync_state`。
  - 全表 ULID 主键或业务指定主键。
  - `observation_event.event_id` 幂等唯一。
  - 软删除字段 `is_deleted`。
  - `audit_log` migration 中加入禁止 UPDATE/DELETE 的数据库权限约束或后续可执行 SQL。
- **测试要求**：
  - Integration：迁移升降级。
  - Schema：关键索引与 unique 约束存在。
- **验收标准**：
  - 空库执行 `alembic upgrade head` 成功。
  - 核心表、索引、FK 与工程设计一致。
- **DoD**：满足通用 DoD；Schema 可支撑后续 Repository 开发。

---

### APC-T005 — 接入结构化日志、Metrics、Tracing 与基础健康端点

- **所属 Epic**：E01
- **所属 Capability**：C03 可观测性与审计
- **所属 Story**：S03 建立日志、指标、追踪、不可删除审计
- **目标**：实现 structlog JSON 日志、Prometheus `/metrics`、OpenTelemetry 基础 tracing、系统健康端点。
- **状态**：DONE
- **前置依赖**：APC-T002
- **输入**：`ENGINEERING_DESIGN.md` §10；`ARCHITECTURE_FINAL.md` §22
- **输出**：可观测性基础设施
- **涉及模块**：observability, gateway, health
- **涉及文件**：
  - 新建：`server/app/observability/logger.py`, `metrics.py`, `tracing.py`
  - 新建：`server/app/health/api.py`
  - 修改：`server/app/main.py`, `server/app/gateway/middleware/logging.py`
- **实现要求**：
  - 日志字段包含：`trace_id, request_id, family_id, baby_id, user_id, actor_kind, module`。
  - PII/raw_input/media path 默认 mask。
  - `/metrics` 暴露工程设计列出的核心指标占位。
  - tracing 可在未启动 Jaeger 时安全降级。
- **测试要求**：
  - Unit：PII mask。
  - Integration：请求日志包含 request_id；`/metrics` 返回 Prometheus 格式。
- **验收标准**：
  - 每次 HTTP 请求有结构化日志。
  - `/healthz` 与 `/metrics` 可访问。
- **DoD**：满足通用 DoD；后续模块可直接记录日志和指标。

---

### APC-T006 — 实现审计日志服务与 `@audit` 装饰器

- **所属 Epic**：E01
- **所属 Capability**：C03
- **所属 Story**：S03
- **目标**：实现不可删除审计写入服务与 mutating API 装饰器。
- **状态**：BLOCKED（service/decorator/unit tests 已完成；audit_log DB insert/update/delete 需 PostgreSQL 验收）
- **前置依赖**：APC-T004, APC-T005
- **输入**：`ENGINEERING_DESIGN.md` §10.4、§14；`ARCHITECTURE_FINAL.md` §1.2、§22.2
- **输出**：Audit service、decorator、数据库写入与测试
- **涉及模块**：observability, common, gateway
- **涉及文件**：
  - 新建：`server/app/observability/audit.py`
  - 新建：`server/app/common/audit_decorator.py`
  - 修改：`server/app/models.py`, `server/migrations/versions/0001_initial_schema.py` 或新增 migration
- **实现要求**：
  - 审计字段：actor, action, resource, before, after, rule_version, llm_call_id, trace_id。
  - 审计写入失败时，mutating 高风险操作不得静默成功。
  - 数据库层禁止普通 app user 更新/删除 audit_log。
- **测试要求**：
  - Unit：decorator 捕获 before/after。
  - Integration：插入 audit_log 成功；UPDATE/DELETE 被拒绝或无可用接口。
- **验收标准**：
  - 任一接入 `@audit` 的测试 API 调用后有审计记录。
  - 审计日志无法通过应用 repository 删除。
- **DoD**：满足通用 DoD；后续写操作可统一接入审计。

---

## Epic E02 — 权限、事件、同步与派生状态

---

### APC-T007 — 实现 Auth/RBAC Domain、Repository 与 JWT 服务

- **所属 Epic**：E02
- **所属 Capability**：C04 Auth/RBAC
- **所属 Story**：S04 家庭账号、角色、设备注册
- **目标**：实现家庭、用户、角色、JWT、RBAC 判定基础能力。
- **状态**：BLOCKED（domain/service/JWT/RBAC/in-memory repo/unit tests 已完成；DB repo 与真实审计验收待 PostgreSQL）
- **前置依赖**：APC-T004, APC-T006
- **输入**：`ENGINEERING_DESIGN.md` §2 M02、§6；`ARCHITECTURE_FINAL.md` §19
- **输出**：Auth domain/service/infra
- **涉及模块**：auth
- **涉及文件**：
  - 新建：`server/app/auth/domain/*.py`, `service/*.py`, `infra/repository.py`
  - 新建：`server/app/auth/tests/test_auth_service.py`
  - 修改：`server/app/di.py`
- **实现要求**：
  - 角色：Admin、Caregiver、Viewer、System。
  - P0 允许 Admin 完整使用；Caregiver/Viewer 可先预留权限表。
  - 密码或 PIN hash 不得明文存储。
  - JWT 包含 user_id、family_id、role、device_id。
- **测试要求**：
  - Unit：密码校验、JWT 签发/解析、RBAC allow/deny。
- **验收标准**：
  - 可创建 family/user。
  - Admin 可通过鉴权依赖获得 Principal。
  - 非授权角色访问受限方法被拒。
- **DoD**：满足通用 DoD；Auth service 可被 API Gateway 使用。

---

### APC-T008 — 实现 Auth API、设备注册与 seed_family 脚本

- **所属 Epic**：E02
- **所属 Capability**：C04
- **所属 Story**：S04
- **目标**：提供登录、刷新、家庭初始化、设备注册 API 与本地种子脚本。
- **状态**：BLOCKED（dev/in-memory API 与 seed 脚本已完成；DB 持久化与 audit_log 集成验收待 PostgreSQL）
- **前置依赖**：APC-T007
- **输入**：`ARCHITECTURE_FINAL.md` §15.2、§19、§25.3
- **输出**：Auth API 与 seed 脚本
- **涉及模块**：auth, gateway
- **涉及文件**：
  - 新建：`server/app/auth/api/routes.py`
  - 新建：`server/scripts/seed_family.py`
  - 修改：`server/app/main.py`, `server/app/gateway/routers/__init__.py`
- **实现要求**：
  - API 前缀 `/api/v1/auth`。
  - 设备注册支持 phone/camera/mmwave/mac。
  - FCM token 存储在 `device.meta` 或独立字段。
  - seed 脚本创建默认 family、父母 Admin、baby 档案。
- **测试要求**：
  - Integration：login → token → protected endpoint。
  - Integration：device registration 写入 DB。
- **验收标准**：
  - `python server/scripts/seed_family.py` 可生成可登录账号。
  - Android 后续可通过 API 注册设备。
- **DoD**：满足通用 DoD；Auth API 可用于端到端 MVP。

---

### APC-T009 — 实现 ObservationEvent 契约、Repository 与幂等写入

- **所属 Epic**：E02
- **所属 Capability**：C05 ObservationEvent 与 Event Store
- **所属 Story**：S05 统一事件写入、幂等、纠错、软删除
- **目标**：实现 ObservationEvent Pydantic 契约、DB Repository、event_id 幂等 upsert。
- **状态**：BLOCKED（Pydantic 契约、idempotency、in-memory repo/unit tests 已完成；DB repository/upsert 集成验收待 PostgreSQL）
- **前置依赖**：APC-T004, APC-T008
- **输入**：`ENGINEERING_DESIGN.md` §5.1、§6.1；`ARCHITECTURE_FINAL.md` §6.2、§6.3
- **输出**：事件领域模型与 Repository
- **涉及模块**：events
- **涉及文件**：
  - 新建：`server/app/events/domain/observation_event.py`
  - 新建：`server/app/events/infra/repository.py`
  - 新建：`server/app/events/service/idempotency.py`
  - 新建：`server/app/events/tests/test_event_repository.py`
- **实现要求**：
  - Source 枚举：manual, voice_text, camera, sensor, ai, system。
  - 区分 `sync_status` 与 `processing_status`。
  - 重复 event_id 不创建重复记录。
  - correction_of 与 is_deleted 字段保留。
- **测试要求**：
  - Unit：Pydantic 校验。
  - Integration：重复 upsert 幂等。
- **验收标准**：
  - 合法同步契约事件可写入。
  - 重复写入返回同一 event_id。
- **DoD**：满足通用 DoD；事件可被 API/Sync/Normalization 共用。

---

### APC-T010 — 实现 Events API：创建、查询、纠错、软删除

- **所属 Epic**：E02
- **所属 Capability**：C05
- **所属 Story**：S05
- **目标**：提供 `/api/v1/events` 写入与查询能力，支持纠错链和软删除。
- **前置依赖**：APC-T009, APC-T006
- **输入**：`ARCHITECTURE_FINAL.md` §5.1、§9.2、§15.2
- **输出**：Events API
- **涉及模块**：events, gateway, observability
- **涉及文件**：
  - 新建：`server/app/events/api/routes.py`
  - 新建：`server/app/events/service/event_service.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - 写接口以 event_id 幂等。
  - 编辑不覆盖历史，应创建 correction 关系或保留版本信息。
  - 删除只设置 `is_deleted=true`。
  - 所有 mutating 操作接入 `@audit`。
- **测试要求**：
  - Integration：create/query/correction/soft delete。
  - Audit：每次 mutating 操作产生审计。
- **验收标准**：
  - 同一 family/baby 下可查询事件时间线。
  - 被软删除事件默认不出现在普通查询中，但审计可追溯。
- **DoD**：满足通用 DoD；Timeline 后续可复用该 API。

---

### APC-T011 — 实现 PG LISTEN/NOTIFY 事件总线与事件变更触发器

- **所属 Epic**：E02
- **所属 Capability**：C06 同步与事件总线
- **所属 Story**：S06 PowerSync 写入契约、PG LISTEN/NOTIFY
- **目标**：实现轻量事件总线，使 observation_event 变更触发 Normalization worker。
- **前置依赖**：APC-T009
- **输入**：`ENGINEERING_DESIGN.md` §6.3、§7.1；`ARCHITECTURE_FINAL.md` §4.1
- **输出**：PG trigger、LISTEN/NOTIFY 封装、worker 消费基座
- **涉及模块**：common, events, normalization
- **涉及文件**：
  - 新建：`server/app/common/event_bus.py`
  - 新建：`server/migrations/versions/0002_event_notify_trigger.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - NOTIFY channel 至少包含 `events.changed`。
  - Payload 包含 event_id、baby_id、operation。
  - 消费采用 at-least-once，业务必须幂等。
  - Worker 崩溃恢复依赖 `processing_status=pending` 扫描。
- **测试要求**：
  - Integration：插入 observation_event 后收到 NOTIFY。
  - Unit：payload parse。
- **验收标准**：
  - 本地 dev 启动后 worker 能订阅并打印事件变更日志。
- **DoD**：满足通用 DoD；Normalization 可接入事件总线。

---

### APC-T012 — 实现 PowerSync 适配、同步契约校验与冲突软提示基础

- **所属 Epic**：E02
- **所属 Capability**：C06
- **所属 Story**：S06
- **目标**：提供 PowerSync 配置、同步表定义、服务端写入契约校验与基础冲突检测。
- **前置依赖**：APC-T003, APC-T009
- **输入**：`ENGINEERING_DESIGN.md` §2 M03、§4、§6.2；`ARCHITECTURE_FINAL.md` §9
- **输出**：PowerSync schema/config、Sync service、冲突提示表或接口
- **涉及模块**：sync, events
- **涉及文件**：
  - 新建：`server/app/sync/service/contract_validator.py`
  - 新建：`server/app/sync/infra/powersync_config.yaml`
  - 新建：`server/app/sync/tests/test_contract_validator.py`
  - 修改：`deploy/docker-compose.yml`
- **实现要求**：
  - 不自研同步引擎。
  - 校验每条同步记录包含架构 §6.3 字段。
  - 5 分钟内疑似重复喂奶仅生成软提示，不自动删除。
  - pending_sync 与 processing_status 独立推进。
- **测试要求**：
  - Unit：契约缺字段拒绝。
  - Integration：模拟重复 feeding 生成 conflict hint。
- **验收标准**：
  - PowerSync 服务可读取配置启动。
  - 非法同步事件不会进入业务处理。
- **DoD**：满足通用 DoD；Android Sync 可据此对接。

---

### APC-T013 — 实现 Normalization 表单/语音文本解析与领域派生表写入

- **所属 Epic**：E02
- **所属 Capability**：C07 Normalization
- **所属 Story**：S07 多源输入归一化为领域派生表
- **目标**：将 manual/form/voice_text ObservationEvent 归一化为 feeding/diaper/sleep/temperature/supplement 等 P0 派生表。
- **前置依赖**：APC-T009, APC-T011
- **输入**：`ENGINEERING_DESIGN.md` §2 M05、§3 normalization、§7.1
- **输出**：Normalization parser 与 table writer
- **涉及模块**：normalization, events
- **涉及文件**：
  - 新建：`server/app/normalization/parsers/form.py`, `voice.py`
  - 新建：`server/app/normalization/service.py`
  - 新建：`server/app/normalization/tests/test_normalization_p0.py`
- **实现要求**：
  - 不做医疗判断。
  - 写派生表必须保留 event_id FK 溯源。
  - confidence 默认 manual=1.0，voice_text 可低于 1.0。
  - 不识别事件保留为 observation_event，标记 processing_status。
- **测试要求**：
  - Unit：feeding、diaper、temperature、sleep event 解析。
  - Integration：事件入库后写入对应派生表。
- **验收标准**：
  - P0 记录类型可成功归一化。
  - 派生表可追溯原始 event_id。
- **DoD**：满足通用 DoD；State Engine 可消费派生表。

---

### APC-T014 — 实现去重、纠错链处理与 Normalization Worker

- **所属 Epic**：E02
- **所属 Capability**：C07
- **所属 Story**：S07
- **目标**：实现 Normalization 常驻 worker、去重策略、纠错/软删除对派生表的处理。
- **前置依赖**：APC-T013
- **输入**：`ENGINEERING_DESIGN.md` §6.3、§7.1、§12.2
- **输出**：Normalization worker 与幂等处理逻辑
- **涉及模块**：normalization, events, state_engine
- **涉及文件**：
  - 新建：`server/app/normalization/dedup.py`
  - 修改：`server/app/normalization/service.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - Worker 消费 `events.changed`。
  - 重复消息不会重复写派生表。
  - correction_of 触发旧派生记录失效或新版本生效。
  - soft delete 触发派生表排除。
- **测试要求**：
  - Unit：dedup 规则。
  - Integration：重复 NOTIFY 只处理一次。
  - Integration：纠错事件更新派生结果。
- **验收标准**：
  - processing_status 可从 pending 推进到 normalized。
  - 崩溃恢复扫描 pending 事件可补处理。
- **DoD**：满足通用 DoD；Normalization 可稳定运行。

---

### APC-T015 — 实现 Baby State Engine P0 Projection

- **所属 Epic**：E02
- **所属 Capability**：C08 Baby State Engine
- **所属 Story**：S08 幂等增量派生 DerivedBabyState
- **目标**：实现 feeding、diaper、sleep、temperature、supplement P0 派生计算。
- **前置依赖**：APC-T013
- **输入**：`ENGINEERING_DESIGN.md` §2 M06、§3 state_engine；`ARCHITECTURE_FINAL.md` §10.1
- **输出**：State projection 纯函数
- **涉及模块**：state_engine
- **涉及文件**：
  - 新建：`server/app/state_engine/projections/feeding.py`, `diaper.py`, `sleep.py`, `temperature.py`, `supplement.py`
  - 新建：`server/app/state_engine/tests/test_projections.py`
- **实现要求**：
  - 派生状态只做计算，不产生告警等级。
  - 计算项至少包括：距上次喂奶、24h 奶量/次数、湿/脏尿布数、24h 睡眠、当前会话、24h 最高温。
  - 所有 projection 应为可单测纯函数或近似纯函数。
- **测试要求**：
  - Unit：各 projection 边界场景。
  - Property：事件顺序变换后结果一致。
- **验收标准**：
  - 给定 fixture 事件集输出稳定 DerivedBabyState。
- **DoD**：满足通用 DoD；projection 覆盖率目标 ≥95%。

---

### APC-T016 — 实现 State Engine 增量重算、Snapshot Repo 与 State API

- **所属 Epic**：E02
- **所属 Capability**：C08
- **所属 Story**：S08
- **目标**：实现派生状态重算服务、`derived_baby_state` upsert、`GET /babies/{id}/state`。
- **前置依赖**：APC-T015, APC-T006
- **输入**：`ENGINEERING_DESIGN.md` §6.3、§7.1
- **输出**：StateEngine service、snapshot repository、API
- **涉及模块**：state_engine, gateway
- **涉及文件**：
  - 新建：`server/app/state_engine/engine.py`, `snapshot_repo.py`
  - 新建：`server/app/state_engine/api/routes.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - 重算必须幂等。
  - 支持按 baby_id 全量重算与事件触发增量重算。
  - snapshot JSONB 包含 computed_at 与 source event range。
  - state API 只读。
- **测试要求**：
  - Integration：事件 → 重算 → snapshot upsert。
  - API：鉴权后查询 state。
- **验收标准**：
  - `GET /api/v1/babies/{id}/state` 返回最新 DerivedBabyState。
- **DoD**：满足通用 DoD；Today 首页可消费此 API。

---

### APC-T017 — 打通 Event → Normalization → State 集成链路

- **所属 Epic**：E02
- **所属 Capability**：C08
- **所属 Story**：S08
- **目标**：完成服务端记录路径集成测试：事件写入后自动归一化并生成派生态。
- **前置依赖**：APC-T010, APC-T014, APC-T016
- **输入**：`ENGINEERING_DESIGN.md` §7.1；`ARCHITECTURE_FINAL.md` §4.1
- **输出**：关键路径集成测试与必要 glue code
- **涉及模块**：events, normalization, state_engine, observability
- **涉及文件**：
  - 新建：`server/tests/integration/test_event_to_state_pipeline.py`
  - 修改：`server/app/main.py`, `server/app/di.py`
- **实现要求**：
  - 使用真实 Postgres/testcontainers。
  - 不 mock DB。
  - Worker 可在测试中手动驱动或后台运行。
- **测试要求**：
  - Integration：feeding event 写入 → feeding_log → derived_baby_state。
  - Integration：soft delete 后 snapshot 更新。
- **验收标准**：
  - MVP 服务端记录链路自动完成。
  - 测试可重复运行无脏数据依赖。
- **DoD**：满足通用 DoD；作为 P0-M0 地基验收项。

---

## Epic E03 — Rule Engine、AI 编排与安全输出

---

### APC-T018 — 实现 Rule Engine Kernel、Loader、Registry 与 EvidencePolicy Repo

- **所属 Epic**：E03
- **所属 Capability**：C09 Rule Engine Kernel
- **所属 Story**：S09 规则加载、注册、EvidencePolicy 版本化
- **目标**：实现规则引擎基础抽象、YAML 加载、EvidencePolicy 持久化与规则注册。
- **状态**：BLOCKED（kernel/loader/registry/in-memory EvidencePolicy repo/rules-validate 已完成；DB persistence/audit 待 PostgreSQL）
- **前置依赖**：APC-T004, APC-T006
- **输入**：`ENGINEERING_DESIGN.md` §5.3、§6、§13.2
- **输出**：Rule Engine kernel 可加载 YAML 并执行空/示例规则
- **涉及模块**：rule_engine
- **涉及文件**：
  - 新建：`server/app/rule_engine/kernel.py`, `loader.py`, `registry.py`, `evidence_repo.py`
  - 新建：`server/app/rule_engine/domain/models.py`
  - 新建：`config/rules/README.md`
- **实现要求**：
  - RuleResult 必须包含 verdict、outputs、evidence、rule_version、reason_code。
  - 规则包版本化，hash 可校验。
  - 当前生效 EvidencePolicy 支持缓存但写入后必须失效。
- **测试要求**：
  - Unit：YAML schema 校验、hash、registry。
  - Golden：示例规则输入输出。
- **验收标准**：
  - `make rules-validate` 可校验规则包。
  - RuleRegistry 能按 domain 调用 RuleModule。
- **DoD**：满足通用 DoD；后续规则域可插件化接入。

---

### APC-T019 — 实现规则 Admin API：validate / activate / audit

- **所属 Epic**：E03
- **所属 Capability**：C09
- **所属 Story**：S09
- **目标**：提供规则包验证、激活与审计记录能力。
- **前置依赖**：APC-T018, APC-T008
- **输入**：`ENGINEERING_DESIGN.md` §13.2；`ARCHITECTURE_FINAL.md` §18、§19
- **输出**：Rules Admin API
- **涉及模块**：rule_engine, auth, observability
- **涉及文件**：
  - 新建：`server/app/rule_engine/api/routes.py`
  - 修改：`server/app/main.py`, `Makefile`
- **实现要求**：
  - API 前缀 `/api/v1/rules`。
  - 规则变更仅 Admin 可执行。
  - 激活新版本时旧版本 `effective_to` 自动关闭。
  - 每次变更写 audit_log。
- **测试要求**：
  - Integration：非 Admin 被拒。
  - Integration：激活新版本后旧版本失效。
- **验收标准**：
  - 可通过 API 激活规则包并追溯变更人/版本。
- **DoD**：满足通用 DoD；规则治理闭环可用。

---

### APC-T020 — 实现 Medication Rule Domain 与黄金测试

- **所属 Epic**：E03
- **所属 Capability**：C10 规则域
- **所属 Story**：S10 用药、分诊、阈值、疫苗、生长规则
- **目标**：实现 P0/V1 用药规则：体重、月龄、浓度、间隔、24h 上限、防重复。
- **状态**：BLOCKED（MedicationRuleModule/规则包/golden tests 已完成；前置 T018 仍待 DB/audit 验收）
- **前置依赖**：APC-T018
- **输入**：`ENGINEERING_DESIGN.md` §7.4；`ARCHITECTURE_FINAL.md` §4.4、§10.2
- **输出**：Medication RuleModule、规则 YAML、golden tests
- **涉及模块**：rule_engine/domains/medication
- **涉及文件**：
  - 新建：`server/app/rule_engine/domains/medication.py`
  - 新建：`config/rules/medication/base.yaml`
  - 新建：`server/tests/golden/rules/test_medication_rules.py`
- **实现要求**：
  - 未知体重不出剂量。
  - 未知浓度不出 ml。
  - 体重过旧要求更新。
  - `<6` 月龄布洛芬默认 block。
  - 接近 24h 上限阻止重复。
  - 所有 dose 输出只能来自 RuleResult。
- **测试要求**：
  - Golden 覆盖 allow/block/warn。
  - Unit 覆盖边界年龄、体重缺失、浓度缺失。
- **验收标准**：
  - 所有用药硬拦截场景输出符合架构。
  - RuleResult 包含 evidence 与 rule_version。
- **DoD**：满足通用 DoD；该模块覆盖率目标 ≥95%。

---

### APC-T021 — 实现 Triage 与 Alert Threshold Rule Domain

- **所属 Epic**：E03
- **所属 Capability**：C10
- **所属 Story**：S10
- **目标**：实现分诊红线、危险信号、体温阈值、趋势告警双条件规则。
- **状态**：BLOCKED（Triage/Threshold pure rule modules/golden tests 已完成；前置 T018/T016 未 DONE）
- **前置依赖**：APC-T018, APC-T016
- **输入**：`ARCHITECTURE_FINAL.md` §10.2、§12；`ENGINEERING_DESIGN.md` §7.3
- **输出**：Triage/Threshold RuleModules 与规则包
- **涉及模块**：rule_engine, notification
- **涉及文件**：
  - 新建：`server/app/rule_engine/domains/triage.py`, `thresholds.py`
  - 新建：`config/rules/triage/base.yaml`, `config/alert_thresholds.yaml`
  - 新建：`server/tests/golden/rules/test_triage_rules.py`, `test_threshold_rules.py`
- **实现要求**：
  - 3 月龄以下 ≥38°C 强红线。
  - 趋势类黄/橙默认连续 N 天 + 偏离 X% 双条件。
  - mmWave 单信号不得产生红色医疗告警。
  - 输出 Alert candidate 时必须携带 evidence。
- **测试要求**：
  - Golden：红/橙/黄/蓝/灰场景。
  - Unit：双条件阈值。
- **验收标准**：
  - 高风险分诊可输出红/橙告警候选。
  - 趋势单点异常不会误触发强提醒。
- **DoD**：满足通用 DoD；安全规则测试先于业务接入完成。

---

### APC-T022 — 实现 Vaccine Planner Rule Domain

- **所属 Epic**：E03
- **所属 Capability**：C10
- **所属 Story**：S10
- **目标**：实现中国疫苗规则 P0：计划、逾期、已完成记录与 EvidencePolicy 版本化。
- **状态**：BLOCKED（VaccineRuleModule/规则包/golden tests 已完成；前置 T018 与生产规则审查未完成）
- **前置依赖**：APC-T018
- **输入**：`ARCHITECTURE_FINAL.md` §10.2、§11.4；`ENGINEERING_DESIGN.md` §13.2
- **输出**：Vaccine RuleModule、规则包、golden tests
- **涉及模块**：rule_engine/domains/vaccine
- **涉及文件**：
  - 新建：`server/app/rule_engine/domains/vaccine.py`
  - 新建：`config/rules/vaccine/cn-nip-2024.yaml`
  - 新建：`server/tests/golden/rules/test_vaccine_rules.py`
- **实现要求**：
  - baby.vaccine_region 默认 CN。
  - 支持 planned/completed/delayed/skipped 状态输入。
  - 输出应包含 due date、status、evidence。
- **测试要求**：
  - Golden：出生后常见计划、逾期、已接种跳过。
- **验收标准**：
  - 给定 baby birth_date 可生成 P0 疫苗待办。
- **DoD**：满足通用 DoD；Scheduler 可消费疫苗到期结果。

---

### APC-T023 — 实现 Growth Rule Domain 与 WHO 百分位基础

- **所属 Epic**：E03
- **所属 Capability**：C10
- **所属 Story**：S10
- **目标**：实现 WHO 0–5 岁基础生长百分位计算与趋势提示规则。
- **状态**：BLOCKED（GrowthRuleModule/简化 WHO fixture/golden tests 已完成；前置 T018 与完整 WHO 表验收未完成）
- **前置依赖**：APC-T018
- **输入**：`ARCHITECTURE_FINAL.md` §10.2、§11.4
- **输出**：Growth RuleModule、WHO 配置、golden tests
- **涉及模块**：rule_engine/domains/growth
- **涉及文件**：
  - 新建：`server/app/rule_engine/domains/growth.py`
  - 新建：`config/rules/growth/who-0-5.yaml`
  - 新建：`server/tests/golden/rules/test_growth_rules.py`
- **实现要求**：
  - 按性别、日龄/月龄计算。
  - P0 可实现简化 fixture 数据，但接口需兼容完整 WHO 表。
  - 趋势提醒不得单点强告警。
- **测试要求**：
  - Golden：男/女、不同月龄、边界百分位。
- **验收标准**：
  - Growth API/Rule 可返回 percentile 与 evidence。
- **DoD**：满足通用 DoD；Growth Copilot 可消费结果。

---

### APC-T024 — 实现 Model Gateway Smart Proxy 客户端与 Routing Plan

- **所属 Epic**：E03
- **所属 Capability**：C11 Model / Privacy / Memory 适配
- **所属 Story**：S11 复用工厂模型、隐私、Local RAG 能力
- **目标**：实现项目内唯一 LLM/VLM 入口，调用工厂 Smart Proxy 4000。
- **状态**：DONE
- **前置依赖**：APC-T002, APC-T005
- **输入**：`ENGINEERING_DESIGN.md` §5.8、§8；工厂根目录 `../../../PROJECT_DOSSIER_V5.md` §4.2、§6
- **输出**：ModelClient、routing plan loader、FakeModelClient
- **涉及模块**：model_gateway
- **涉及文件**：
  - 新建：`server/app/model_gateway/client.py`, `routing.py`
  - 新建：`config/routing_plans.yaml`, `config/models.yaml`
  - 新建：`server/app/model_gateway/tests/test_model_gateway.py`
- **实现要求**：
  - 禁止任何模块直连云模型。
  - 支持 `chat(plan, messages)` 与 `vision(plan, image, prompt)`。
  - 文本超时 30s，视觉超时 60s。
  - 测试默认使用 FakeModelClient，CI 禁调真实模型。
- **测试要求**：
  - Unit：routing plan 解析。
  - Unit：timeout/fallback 行为。
- **验收标准**：
  - Orchestrator/Copilot 后续只能注入 ModelClient。
- **DoD**：满足通用 DoD；模型调用路径符合 Factory-first。

---

### APC-T025 — 实现 Privacy Gateway 适配层与云出站安全测试

- **所属 Epic**：E03
- **所属 Capability**：C11
- **所属 Story**：S11
- **目标**：通过适配层复用工厂 `_infra/network/privacy`，在云端出站前执行脱敏与 canary 检查。
- **状态**：DONE
- **前置依赖**：APC-T024
- **输入**：`ENGINEERING_DESIGN.md` §2 M14、§8；工厂根目录 `../../../PROJECT_DOSSIER_V5.md` §5.4
- **输出**：Privacy adapter、安全测试
- **涉及模块**：privacy, model_gateway
- **涉及文件**：
  - 新建：`server/app/privacy/adapter.py`
  - 新建：`config/privacy_policy.yaml`
  - 新建：`server/tests/security/test_privacy_adapter.py`
  - 修改：`server/app/model_gateway/client.py`
- **实现要求**：
  - 不复制工厂 privacy 实现。
  - 云端 route 必须先调用 privacy adapter。
  - 视频/图片/音频/原始媒体不得发往云端。
  - canary 泄露测试必须失败阻断。
- **测试要求**：
  - Security：PII 脱敏、canary 阻断、媒体出站阻断。
- **验收标准**：
  - 模拟云 route 时，原始姓名/电话/地址等 PII 不出站。
- **DoD**：满足通用 DoD；隐私边界可审计。

---

### APC-T026 — 实现 Memory Store M1-M5 与 Local RAG 适配

- **所属 Epic**：E03
- **所属 Capability**：C11
- **所属 Story**：S11
- **目标**：实现五层记忆读取与上下文快照生成，M5 复用工厂 Local RAG。
- **状态**：BLOCKED（M1-M5 snapshot/in-memory MemoryStore 已完成；State Engine 与 Local RAG 真实适配待前置解除）
- **前置依赖**：APC-T016, APC-T025
- **输入**：`ENGINEERING_DESIGN.md` §5.9；`ARCHITECTURE_FINAL.md` §6.5
- **输出**：MemoryStore、MemorySnapshot、injector
- **涉及模块**：memory
- **涉及文件**：
  - 新建：`server/app/memory/m1_hard_facts.py`, `m2_family_prefs.py`, `m3_baseline.py`, `m4_short_context.py`, `m5_correction.py`, `injector.py`
  - 新建：`server/app/memory/tests/test_memory_store.py`
- **实现要求**：
  - M1/M2/M3/M4 优先结构化查询。
  - M5 可调用 Local RAG adapter，不复制实现。
  - 健康类上下文必须包含日龄、体重、近72h、过敏史、规则版本占位。
- **测试要求**：
  - Unit：各层 memory 返回结构。
  - Integration：MemorySnapshot 构建。
- **验收标准**：
  - Orchestrator 可一次性获取完整 CopilotContext 所需 memory。
- **DoD**：满足通用 DoD；上下文注入可复用。

---

### APC-T027 — 实现 Copilot Base、Registry 与 Logger Copilot

- **所属 Epic**：E03
- **所属 Capability**：C12 Orchestrator & Copilots
- **所属 Story**：S12 意图路由、上下文注入、Dose Interceptor、P0 Copilots
- **目标**：实现 DomainCopilot 协议、注册表与 P0 Logger Copilot。
- **状态**：BLOCKED（Copilot base/registry/logger regex parser/tests 已完成；前置 T026 未 DONE，LLM ModelClient 注入待后续）
- **前置依赖**：APC-T024, APC-T026
- **输入**：`ENGINEERING_DESIGN.md` §5.4、§13.1；`ARCHITECTURE_FINAL.md` §11.4
- **输出**：Copilot 抽象、Registry、Logger Copilot
- **涉及模块**：copilots
- **涉及文件**：
  - 新建：`server/app/copilots/base.py`, `logger_copilot.py`
  - 新建：`server/app/copilots/tests/test_logger_copilot.py`
  - 可选新建：`_factory/skills/parenting/logger.skill.md`
- **实现要求**：
  - Logger Copilot 输出 `record_candidate`，不直接写 DB。
  - 安全等级 low。
  - 自然语言解析可先使用规则/模板，LLM 通过 ModelClient 注入。
  - 输出需 requires_confirmation。
- **测试要求**：
  - Unit：常见中文喂奶/尿布/体温文本解析。
  - Unit：未知输入返回低置信候选。
- **验收标准**：
  - “刚喂了90ml奶” 可生成 feeding record candidate。
- **DoD**：满足通用 DoD；Quick Record 语音候选可调用。

---

### APC-T028 — 实现 Orchestrator、Intent Router、Context Builder 与 Output Guard

- **所属 Epic**：E03
- **所属 Capability**：C12
- **所属 Story**：S12
- **目标**：实现 `/api/v1/copilot/query` 主编排链路。
- **状态**：BLOCKED（IntentRouter/ContextBuilder/OutputGuard/Orchestrator dev API 已完成；T027/T006 未 DONE，Memory/DB/audit 集成待验收）
- **前置依赖**：APC-T027, APC-T006
- **输入**：`ENGINEERING_DESIGN.md` §5.5、§7.3；`ARCHITECTURE_FINAL.md` §11.2
- **输出**：Orchestrator service 与 API
- **涉及模块**：orchestrator, copilots, memory, rule_engine
- **涉及文件**：
  - 新建：`server/app/orchestrator/intent_router.py`, `context_builder.py`, `output_guard.py`, `orchestrator.py`
  - 新建：`server/app/orchestrator/api/routes.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - 意图至少支持：record、question、triage、config、alert_ack。
  - Context Builder 注入 DerivedBabyState + MemorySnapshot。
  - 中/高安全 Copilot 输出必须经 Rule Engine。
  - 输出结构必须包含 evidence。
- **测试要求**：
  - Unit：intent routing。
  - Integration：copilot query → logger candidate。
- **验收标准**：
  - API 可返回结构化 CopilotResponse。
  - 不存在绕过 ModelClient/RuleEngine 的高风险路径。
- **DoD**：满足通用 DoD；Orchestrator 可作为 AI 单一入口。

---

### APC-T029 — 实现 Dose Interceptor 与安全回归测试

- **所属 Epic**：E03
- **所属 Capability**：C12
- **所属 Story**：S12
- **目标**：拦截 LLM/Copilot 自由输出中的具体剂量数字，并写审计。
- **状态**：BLOCKED（DoseInterceptor 纯逻辑与 MemoryAuditSink 测试已完成；前置 T028 与真实 audit_log 写入待验收）
- **前置依赖**：APC-T028
- **输入**：`ENGINEERING_DESIGN.md` §5.5、§9、§14；`ARCHITECTURE_FINAL.md` §11.3
- **输出**：Dose Interceptor、安全测试、审计记录
- **涉及模块**：orchestrator, observability
- **涉及文件**：
  - 新建：`server/app/orchestrator/dose_interceptor.py`
  - 新建：`server/tests/security/test_dose_interceptor.py`
  - 修改：`server/app/orchestrator/orchestrator.py`
- **实现要求**：
  - 匹配 mg/ml/毫升/滴/片 等剂量模式。
  - Rule Engine 结构化 dose 输出不得被误删，但必须标记 source=rule_engine。
  - 拦截替换为固定安全话术。
  - 每次拦截写 audit_log。
- **测试要求**：
  - Security：prompt injection 诱导剂量输出被拦截。
  - Unit：RuleResult 剂量通过、LLM 文本剂量阻断。
- **验收标准**：
  - LLM 输出“给 2.5ml”最终响应不含该剂量。
  - audit_log 记录 dose_intercept。
- **DoD**：满足通用 DoD；剂量安全铁律可验证。

---

### APC-T030 — 实现 P0 Copilots：Proactive、FamilyMemory、Vaccine、Growth、Medication Basic

- **所属 Epic**：E03
- **所属 Capability**：C12
- **所属 Story**：S12
- **目标**：实现 P0 所需低/中安全 Copilot 外壳，调用 Rule Engine 并生成结构化解释。
- **状态**：BLOCKED（P0 Copilot wrappers/tests 已完成；前置 T020/T022/T023/T028/T029 未 DONE，DB/Memory/audit 集成待验收）
- **前置依赖**：APC-T020, APC-T022, APC-T023, APC-T028, APC-T029
- **输入**：`ARCHITECTURE_FINAL.md` §11.4、§26.1
- **输出**：P0 Copilot 实现与单测
- **涉及模块**：copilots, rule_engine, memory
- **涉及文件**：
  - 新建：`server/app/copilots/proactive_copilot.py`, `family_memory.py`, `vaccine_planner.py`, `growth_milestone.py`, `medication_safety.py`
  - 新建：`server/app/copilots/tests/test_p0_copilots.py`
- **实现要求**：
  - Medication Basic 仅记录+间隔提醒；完整用药安全可 V1 扩展。
  - Vaccine/Growth 必须通过 Rule Engine。
  - FamilyMemory 写入 family_knowledge 必须审计。
  - Proactive 不自行生成告警等级。
- **测试要求**：
  - Unit：每个 Copilot 输出结构、evidence、requires_confirmation。
  - Integration：Vaccine/Growth 调用对应 RuleModule。
- **验收标准**：
  - P0 Copilots 可被 Orchestrator registry 选择并返回安全输出。
- **DoD**：满足通用 DoD；P0 AI 能力可用于 App/API。

---

## Epic E04 — 告警、通知、健康与调度

---

### APC-T031 — 实现 Alert Repository、API、确认与反馈

- **所属 Epic**：E04
- **所属 Capability**：C13 Alert Store/API
- **所属 Story**：S13 告警查询、确认、反馈、审计
- **目标**：实现 Alert CRUD 查询、ack、feedback，并接入审计。
- **状态**：BLOCKED（Alert dev repo/API/MemoryAuditSink tests 已完成；前置 T004/T006/T021 未 DONE，DB audit 集成待验收）
- **前置依赖**：APC-T004, APC-T006, APC-T021
- **输入**：`ENGINEERING_DESIGN.md` §6.1、§7.2；`ARCHITECTURE_FINAL.md` §5.3、§14
- **输出**：Alert service/API
- **涉及模块**：notification, observability
- **涉及文件**：
  - 新建：`server/app/notification/alert_repo.py`, `api/routes.py`, `ack_registry.py`
  - 新建：`server/app/notification/tests/test_alert_api.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - Alert 状态：active, acknowledged, resolved, dismissed。
  - Feedback：useful, false_positive, too_sensitive, already_known, ignored。
  - ack 必须记录 ack_by、ack_at、device。
  - feedback 写入 M5 纠错记忆的接口可先预留。
- **测试要求**：
  - Integration：create → list → ack → feedback。
  - Audit：ack/feedback 均有审计。
- **验收标准**：
  - App 可获取告警详情与证据链。
  - 任一确认可改变告警状态。
- **DoD**：满足通用 DoD；Notification Orchestrator 可消费 Alert。

---

### APC-T032 — 实现 Notification Channel 抽象与 FCM/Mac/App/Camera 通道

- **所属 Epic**：E04
- **所属 Capability**：C14 Notification Orchestrator
- **所属 Story**：S14 多通道扇出、送达凭证、升级状态机
- **目标**：实现通知通道协议和 P0 通道适配。
- **状态**：BLOCKED（NotificationChannel/Fake channels/config/tests 已完成；前置 T031 未 DONE，真实 FCM/TTS 待接入）
- **前置依赖**：APC-T031
- **输入**：`ENGINEERING_DESIGN.md` §5.6、§7.2、§13.3
- **输出**：NotificationChannel 实现与 Fake 通道
- **涉及模块**：notification/channels
- **涉及文件**：
  - 新建：`server/app/notification/channels/base.py`, `fcm.py`, `mac_speaker.py`, `app_fullscreen.py`, `camera_speaker.py`
  - 新建：`config/notification.yaml`
  - 新建：`server/app/notification/tests/test_channels.py`
- **实现要求**：
  - FCM payload 仅包含 alert_id/level/type。
  - Mac/Camera speaker 可先用 shell/TTS/mock 实现，但接口稳定。
  - 每次 send 返回 DeliveryReceipt。
  - 测试使用 FakeFCMChannel。
- **测试要求**：
  - Unit：payload 不含敏感详情。
  - Unit：通道失败返回可记录状态。
- **验收标准**：
  - 所有通道实现统一 Protocol。
  - Notification config 可启停通道。
- **DoD**：满足通用 DoD；多通道编排可接入。

---

### APC-T033 — 实现 Notification Orchestrator 扇出与 Delivery Receipt

- **所属 Epic**：E04
- **所属 Capability**：C14
- **所属 Story**：S14
- **目标**：实现按告警等级选择通道、并发扇出、记录 alert_delivery。
- **状态**：BLOCKED（NotificationOrchestrator fan-out/in-memory delivery receipts/tests 已完成；前置 T032 未 DONE，DB delivery repo 待验收）
- **前置依赖**：APC-T032
- **输入**：`ARCHITECTURE_FINAL.md` §14.4；`ENGINEERING_DESIGN.md` §7.2
- **输出**：Notification orchestrator
- **涉及模块**：notification
- **涉及文件**：
  - 新建：`server/app/notification/orchestrator.py`
  - 新建：`server/app/notification/delivery_repo.py`
  - 新建：`server/app/notification/tests/test_notification_orchestrator.py`
- **实现要求**：
  - Red/Orange 必须多通道。
  - Notification 不产生告警等级，只消费 Alert.level。
  - 所有送达结果写 alert_delivery。
  - FCM 失败不能阻断 Mac/Camera 兜底。
- **测试要求**：
  - Unit：不同 level 通道选择。
  - Integration：red alert 生成多条 delivery。
- **验收标准**：
  - 红色告警发送时至少触发 FCM、Mac、App fullscreen；摄像头作为兜底配置可启用。
- **DoD**：满足通用 DoD；告警送达主链路可运行。

---

### APC-T034 — 实现告警升级状态机与确认取消

- **所属 Epic**：E04
- **所属 Capability**：C14
- **所属 Story**：S14
- **目标**：实现 0s/60s/90s 升级策略，任一 ack 后停止所有通道。
- **前置依赖**：APC-T033
- **输入**：`ENGINEERING_DESIGN.md` §7.2；`ARCHITECTURE_FINAL.md` §14.4
- **输出**：Escalation state machine
- **涉及模块**：notification
- **涉及文件**：
  - 新建：`server/app/notification/escalation.py`
  - 新建：`server/app/notification/tests/test_escalation.py`
  - 修改：`server/app/notification/orchestrator.py`
- **实现要求**：
  - 使用 APScheduler 或可测试 async timer。
  - 0s 初始扇出，T+60s Mac 重复，T+90s 手机加强/摄像头兜底。
  - ack 后调用所有通道 cancel。
  - 时间参数来自 `config/notification.yaml`。
- **测试要求**：
  - 使用 freezegun/虚拟时钟测试升级。
  - Integration：ack 后不再升级。
- **验收标准**：
  - 红色告警未确认时按时升级。
  - 任一确认后全部停止并审计。
- **DoD**：满足通用 DoD；红色告警必达策略具备可测实现。

---

### APC-T035 — 实现 Device Health Monitor 与灰色告警

- **所属 Epic**：E04
- **所属 Capability**：C15 Health Monitor & Scheduler
- **所属 Story**：S15 设备健康、晨报、提醒、灰色告警
- **目标**：监测 DB、MQTT、PowerSync、摄像头、mmWave、FCM、NAS 并在 60s 内产生灰色告警。
- **前置依赖**：APC-T031, APC-T033
- **输入**：`ENGINEERING_DESIGN.md` §10.5；`ARCHITECTURE_FINAL.md` §22.5
- **输出**：health probes、monitor、system health API
- **涉及模块**：health, notification
- **涉及文件**：
  - 新建：`server/app/health/probes/db.py`, `mmwave.py`, `camera.py`, `fcm.py`, `nas.py`
  - 新建：`server/app/health/monitor.py`
  - 修改：`server/app/health/api.py`
- **实现要求**：
  - 灰色告警不得与医疗告警混淆。
  - 摄像头离线 60s 内 alert level=gray。
  - device_online metrics 更新。
  - dev 环境允许 mock probe。
- **测试要求**：
  - Unit：probe 状态转换。
  - Integration：probe 失败生成 gray alert。
- **验收标准**：
  - `/api/v1/system/health` 返回服务/设备状态。
  - 连续失败达到阈值后生成灰色告警。
- **DoD**：满足通用 DoD；Today 首页可显示设备健康。

---

### APC-T036 — 实现 Scheduler：晨报、疫苗到期、补剂提醒、健康巡检

- **所属 Epic**：E04
- **所属 Capability**：C15
- **所属 Story**：S15
- **目标**：实现 APScheduler runner 与 P0 定时任务。
- **前置依赖**：APC-T022, APC-T031, APC-T035
- **输入**：`ENGINEERING_DESIGN.md` §2 M20、§7.2
- **输出**：Scheduler jobs
- **涉及模块**：scheduler, notification, rule_engine
- **涉及文件**：
  - 新建：`server/app/scheduler/runner.py`
  - 新建：`server/app/scheduler/jobs/morning_brief.py`, `vaccine_due.py`, `supplement.py`, `health_check.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - Scheduler 与 FastAPI 同进程 worker 启动。
  - 非红/橙提醒可合并进晨报。
  - 疫苗到期调用 Vaccine Rule。
  - 补剂提醒基于 supplement_log/todo 状态。
- **测试要求**：
  - Unit：job 生成 alert/reminder。
  - Integration：scheduler 手动触发。
- **验收标准**：
  - dev 环境可手动运行晨报 job。
  - 疫苗 due 可生成蓝色/黄色提醒。
- **DoD**：满足通用 DoD；P0 proactive reminder 可用。

---

## Epic E05 — 摄像头、mmWave、媒体、导出与备份

---

### APC-T037 — 实现 Sleep Session Domain/API 与 ROI 配置

- **所属 Epic**：E05
- **所属 Capability**：C16 Sleep Session & Camera
- **所属 Story**：S16 睡眠会话、ROI、抓帧、影子模式
- **目标**：实现睡眠会话状态机、会话 API、ROI 保存与查询。
- **前置依赖**：APC-T004, APC-T006
- **输入**：`ARCHITECTURE_FINAL.md` §5.2、§12.3、§15.2
- **输出**：SleepSession service/API
- **涉及模块**：camera, sleep_session
- **涉及文件**：
  - 新建：`server/app/camera/sleep_session.py`, `roi.py`
  - 新建：`server/app/camera/api/routes.py`
  - 新建：`server/app/camera/tests/test_sleep_session.py`
  - 修改：`server/app/main.py`
- **实现要求**：
  - 状态：not_started → active → paused → active → ended。
  - 仅 active 内允许行为分析。
  - ROI 由用户手动配置。
  - mutating 操作审计。
- **测试要求**：
  - Unit：状态机合法/非法转换。
  - Integration：start/pause/resume/end API。
- **验收标准**：
  - 可创建 active session 并保存 ROI。
  - 非 active 会话下分析 worker 不应运行。
- **DoD**：满足通用 DoD；Camera worker 可基于 session gate 执行。

---

### APC-T038 — 实现 Camera RTSP/ISAPI/Fregata 桥接与 Snapshot Mock

- **所属 Epic**：E05
- **所属 Capability**：C16
- **所属 Story**：S16
- **目标**：实现摄像头接入适配层，支持 dev mock snapshot 与真实 RTSP/ISAPI/Fregata 配置。
- **前置依赖**：APC-T037, APC-T035
- **输入**：`ENGINEERING_DESIGN.md` §2 M11、§7.5；`ARCHITECTURE_FINAL.md` §12
- **输出**：Camera adapters
- **涉及模块**：camera
- **涉及文件**：
  - 新建：`server/app/camera/rtsp_client.py`, `isapi_client.py`, `fregata_bridge.py`
  - 新建：`config/devices.yaml`
  - 新建：`server/app/camera/tests/test_camera_adapters.py`
- **实现要求**：
  - dev 支持 fixture video/snapshot。
  - RTSP snapshot timeout 5s。
  - 断线指数退避并报告 health。
  - 厂商云关闭验证可形成运维检查项，但本任务不做网络审计。
- **测试要求**：
  - Unit：devices.yaml 解析。
  - Integration：mock snapshot 成功。
- **验收标准**：
  - `/api/v1/cameras/{id}/snapshot` 在 dev mock 下返回图片。
- **DoD**：满足通用 DoD；摄像头能力具备本地 mock 与真实适配入口。

---

### APC-T039 — 实现 Clip Recorder、多信号 Fusion 与 VLM Dispatcher 影子模式

- **所属 Epic**：E05
- **所属 Capability**：C16
- **所属 Story**：S16
- **目标**：实现事件片段记录、摄像头/mmWave 融合状态机与 VLM 调度影子模式。
- **前置依赖**：APC-T021, APC-T038, APC-T040
- **输入**：`ENGINEERING_DESIGN.md` §7.5；`ARCHITECTURE_FINAL.md` §12.3、§13.2
- **输出**：Camera safety shadow pipeline
- **涉及模块**：camera, mmwave, rule_engine, media
- **涉及文件**：
  - 新建：`server/app/camera/clip_recorder.py`, `fusion.py`, `vlm_dispatcher.py`
  - 新建：`server/tests/integration/test_camera_shadow_pipeline.py`
- **实现要求**：
  - 仅 sleep_session active 内分析。
  - P0 只影子模式，不强提醒。
  - 片段策略：前 15s / 后 30s。
  - mmWave 不单独触发红警。
  - VLM 调用只能经 ModelGateway。
- **测试要求**：
  - Unit：fusion 状态机。
  - Integration：mock camera + mock mmWave 生成 shadow CameraEvent。
- **验收标准**：
  - 影子事件写入 camera_event，且不产生红色强提醒。
- **DoD**：满足通用 DoD；为 7 晚 shadow 验证提供基础。

---

### APC-T040 — 实现 mmWave Frame Parser、Sensor Mapper 与 MQTT Subscriber

- **所属 Epic**：E05
- **所属 Capability**：C17 mmWave & Firmware
- **所属 Story**：S17 MQTT 雷达接入与 ESP32C6 固件
- **目标**：订阅 `baby/radar/telemetry`，解析雷达 JSON，写入 sensor_event / observation_event。
- **前置依赖**：APC-T003, APC-T009, APC-T035
- **输入**：`ENGINEERING_DESIGN.md` §2 M12、§7.5；`ARCHITECTURE_FINAL.md` §13
- **输出**：mmWave adapter
- **涉及模块**：mmwave, events, health
- **涉及文件**：
  - 新建：`server/app/mmwave/frame_parser.py`, `sensor_event_mapper.py`, `mqtt_subscriber.py`
  - 新建：`server/app/mmwave/tests/test_mmwave_parser.py`
  - 修改：`config/devices.yaml`
- **实现要求**：
  - 使用 aiomqtt。
  - topic 白名单来自 devices.yaml。
  - 断线自动重连。
  - P0 仅生成 SensorEvent 与灰色健康告警，不独立红警。
- **测试要求**：
  - Unit：fixture radar_frames.jsonl 解析。
  - Integration：mock MQTT publisher → sensor_event 入库。
- **验收标准**：
  - dev 环境可模拟发布雷达帧并在 DB 查询到 sensor_event。
- **DoD**：满足通用 DoD；mmWave 数据链路可用。

---

### APC-T041 — 实现 ESP32C6 mmWave MQTT 固件基础

- **所属 Epic**：E05
- **所属 Capability**：C17
- **所属 Story**：S17
- **目标**：实现 ESP32C6 固件：串口读取雷达帧、连接 WiFi、发布 MQTT JSON。
- **前置依赖**：APC-T040
- **输入**：`ARCHITECTURE_FINAL.md` §13.1；`ENGINEERING_DESIGN.md` §1.2
- **输出**：PlatformIO 固件工程
- **涉及模块**：firmware/esp32c6
- **涉及文件**：
  - 新建：`firmware/esp32c6/platformio.ini`
  - 新建：`firmware/esp32c6/src/main.cpp`
  - 新建：`firmware/esp32c6/config.h.example`
  - 新建：`firmware/esp32c6/README.md`
- **实现要求**：
  - 使用 PubSubClient。
  - 配置不提交真实 WiFi/MQTT 密码。
  - Payload 字段：presence/state/breathing_rate/heart_rate/abnormal_event/timestamp。
  - 串口帧协议如未确定，先实现 mock/simple parser 并文档标注。
- **测试要求**：
  - `pio run` 编译通过。
  - 可选串口 parser 单测。
- **验收标准**：
  - 固件可编译。
  - README 说明烧录、配置与 MQTT topic。
- **DoD**：满足通用 DoD；硬件接入具备基础固件。

---

### APC-T042 — 实现加密 Media Storage、Thumbnail 与 Media API

- **所属 Epic**：E05
- **所属 Capability**：C18 Media / Export / Backup
- **所属 Story**：S18 加密媒体、MD/PDF 导出、NAS 备份
- **目标**：实现本地媒体加密存储、缩略图、asset 索引与上传/读取 API。
- **前置依赖**：APC-T004, APC-T006
- **输入**：`ENGINEERING_DESIGN.md` §2 M16、§11；`ARCHITECTURE_FINAL.md` §8
- **输出**：Media storage service/API
- **涉及模块**：media
- **涉及文件**：
  - 新建：`server/app/media/storage.py`, `thumbnails.py`, `api/routes.py`
  - 新建：`server/app/media/tests/test_media_storage.py`
  - 修改：`.env.example`
- **实现要求**：
  - AES-GCM 加密。
  - 大文件不入库，只保存 metadata/path。
  - 缩略图存 `runtime/media/thumbs/`。
  - 原始音频如转文本后可删除策略预留。
- **测试要求**：
  - Unit：加解密 roundtrip。
  - Integration：上传文件生成 media_asset。
- **验收标准**：
  - 上传图片后 DB 有 media_asset，文件加密存储，缩略图可生成。
- **DoD**：满足通用 DoD；Camera/Jaundice/Export 可复用媒体服务。

---

### APC-T043 — 实现 Export MD/PDF 与就诊摘要基础

- **所属 Epic**：E05
- **所属 Capability**：C18
- **所属 Story**：S18
- **目标**：按时间范围导出 MD/PDF、基础统计与就诊摘要，并审计导出人/时间。
- **前置依赖**：APC-T016, APC-T042
- **输入**：`ARCHITECTURE_FINAL.md` §8、§15.2、§21
- **输出**：Export service/API
- **涉及模块**：export, media
- **涉及文件**：
  - 新建：`server/app/export/service.py`
  - 新建：`server/app/media/export/markdown.py`, `pdf.py`
  - 新建：`server/app/export/api/routes.py`
  - 新建：`server/app/export/tests/test_export_service.py`
- **实现要求**：
  - API：`POST /api/v1/export`，range=7d/30d，format=md/pdf。
  - 导出文件存本地 file store。
  - 导出必须审计。
  - PDF 可先使用成熟库或简化 HTML→PDF；若依赖不可用，至少 MD 完整、PDF 占位需测试标明。
- **测试要求**：
  - Integration：生成 7d MD。
  - Unit：导出内容不含未授权敏感字段。
- **验收标准**：
  - 用户可生成并下载 MD 导出。
  - audit_log 记录导出行为。
- **DoD**：满足通用 DoD；P0 基础导出可用。

---

### APC-T044 — 实现 Backup：PG dump、媒体归档、launchd 与恢复演练文档

- **所属 Epic**：E05
- **所属 Capability**：C18
- **所属 Story**：S18
- **目标**：实现数据库与媒体备份任务，提供 launchd plist 与恢复演练流程。
- **前置依赖**：APC-T003, APC-T042
- **输入**：`ARCHITECTURE_FINAL.md` §24；`ENGINEERING_DESIGN.md` §2 M19
- **输出**：Backup scripts/service/docs
- **涉及模块**：backup, deploy
- **涉及文件**：
  - 新建：`server/app/backup/pg_dump_task.py`, `media_archive.py`
  - 新建：`deploy/launchd/com.parenting.backup.plist`
  - 新建：`docs/RUNBOOK_BACKUP_RESTORE.md`
- **实现要求**：
  - 备份目标可配置 NAS 路径。
  - 不备份明文密钥。
  - 媒体归档保持加密文件。
  - 恢复流程必须可人工执行。
- **测试要求**：
  - Unit：备份路径与保留策略。
  - Integration：dev DB pg_dump 文件生成。
- **验收标准**：
  - 手动运行 backup task 生成 PG dump。
  - 文档说明如何恢复到空库。
- **DoD**：满足通用 DoD；生产前恢复演练具备依据。

---

## Epic E06 — Android 应用

---

### APC-T045 — 初始化 React Native Android-only 应用壳、主题、导航与 API Client

- **所属 Epic**：E06
- **所属 Capability**：C19 Android 基础与同步
- **所属 Story**：S19 RN Android-only 壳、Auth、PowerSync、离线写入
- **目标**：创建 Android-only React Native 应用基础壳，接入导航、主题、API client。
- **前置依赖**：APC-T001, APC-T008
- **输入**：`ENGINEERING_DESIGN.md` §2 安卓端模块、§3；`ARCHITECTURE_FINAL.md` §3.2
- **输出**：可运行 Android App skeleton
- **涉及模块**：android shell
- **涉及文件**：
  - 新建：`android/package.json`, `android/src/App.tsx`, `android/src/navigation/*`, `android/src/theme/*`
  - 新建：`android/src/api/client.ts`
  - 修改：`android/android/*` Gradle 工程文件
- **实现要求**：
  - Android-only，不做 iOS。
  - API client 支持 base URL 配置。
  - 主题支持暗色/夜间模式基础。
- **测试要求**：
  - Android unit：API client base URL。
  - 构建：`./gradlew assembleDebug`。
- **验收标准**：
  - App 可启动显示空壳导航。
  - 能请求 server `/healthz`。
- **DoD**：满足通用 DoD；后续功能页面可接入。

---

### APC-T046 — 实现 Android Auth、家庭切换与设备注册

- **所属 Epic**：E06
- **所属 Capability**：C19
- **所属 Story**：S19
- **目标**：实现登录、token 保存、家庭/宝宝上下文、设备注册。
- **前置依赖**：APC-T045, APC-T008
- **输入**：`ARCHITECTURE_FINAL.md` §3.2、§19
- **输出**：Android Auth feature
- **涉及模块**：android/features/auth
- **涉及文件**：
  - 新建：`android/src/features/auth/*`
  - 新建：`android/src/state/session.ts`
  - 修改：`android/src/api/client.ts`, `android/src/navigation/*`
- **实现要求**：
  - token 安全存储。
  - 登录后调用 device registration。
  - P0 默认单 family，可预留切换。
- **测试要求**：
  - Unit：session reducer/store。
  - Mock API：login/register device flow。
- **验收标准**：
  - 用户可登录并进入主界面。
  - server device 表有 phone 设备记录。
- **DoD**：满足通用 DoD；Android 可参与端到端 MVP。

---

### APC-T047 — 实现 Android op-sqlite + PowerSync Schema 与 pending_sync

- **所属 Epic**：E06
- **所属 Capability**：C19
- **所属 Story**：S19
- **目标**：实现 Android 本地 SQLite、PowerSync client、ObservationEvent 本地写入与 pending_sync 标记。
- **前置依赖**：APC-T012, APC-T046
- **输入**：`ENGINEERING_DESIGN.md` §1.2 Android、§7.1；`ARCHITECTURE_FINAL.md` §9
- **输出**：Android Sync module
- **涉及模块**：android/sync
- **涉及文件**：
  - 新建：`android/src/sync/powersync_client.ts`, `schema.ts`, `local_event_store.ts`
  - 新建：`android/src/sync/tests/*`
- **实现要求**：
  - 离线写入本地即成功。
  - 每条记录含同步契约字段。
  - pending_sync 状态在 UI 可查询。
  - PowerSync 恢复网络后自动补传。
- **测试要求**：
  - Unit：本地 event insert。
  - Integration/mock：offline insert → pending。
- **验收标准**：
  - 断网时 Quick Record 后续可写本地 event。
  - 本地事件包含 event_id/user_id/device_id/source/confidence。
- **DoD**：满足通用 DoD；离线记录地基完成。

---

### APC-T048 — 实现 Android Quick Record P0

- **所属 Epic**：E06
- **所属 Capability**：C20 Android 核心页面
- **所属 Story**：S20 Quick Record、Today、Timeline、Alert Center
- **目标**：实现大按钮快捷记录、计时器、语音文本候选与一次轻确认。
- **前置依赖**：APC-T027, APC-T047
- **输入**：`ARCHITECTURE_FINAL.md` §4.1、§3.2；`ENGINEERING_DESIGN.md` §7.1
- **输出**：Quick Record feature
- **涉及模块**：android/features/quick_record
- **涉及文件**：
  - 新建：`android/src/features/quick_record/*`
  - 修改：`android/src/navigation/*`
- **实现要求**：
  - P0 支持 feeding、diaper、temperature、sleep manual。
  - 写本地 SQLite，不等待网络。
  - 语音可先使用文本输入模拟，调用 Copilot 获取 candidate。
  - 用户确认一次后写入。
- **测试要求**：
  - Unit：payload 构造。
  - Detox：离线 feeding 记录成功显示 pending。
- **验收标准**：
  - 用户 1 次确认可完成 feeding 记录。
  - UI 即时反馈，不依赖 server 在线。
- **DoD**：满足通用 DoD；MVP 记录入口可用。

---

### APC-T049 — 实现 Android Today 首页

- **所属 Epic**：E06
- **所属 Capability**：C20
- **所属 Story**：S20
- **目标**：展示 DerivedBabyState、统计、待办、告警、同步态、设备健康。
- **前置依赖**：APC-T016, APC-T035, APC-T047
- **输入**：`ARCHITECTURE_FINAL.md` §3.2、§22.5
- **输出**：Today feature
- **涉及模块**：android/features/today
- **涉及文件**：
  - 新建：`android/src/features/today/*`
  - 修改：`android/src/navigation/*`
- **实现要求**：
  - 优先读本地 PowerSync 副本，必要时 REST fallback。
  - 显示 pending_sync 数量。
  - 显示设备健康灰色状态。
  - 夜间模式可读。
- **测试要求**：
  - Unit：state view model。
  - UI：空状态、正常状态、pending 状态。
- **验收标准**：
  - feeding 记录同步后 Today 显示距上次喂奶/24h 统计。
- **DoD**：满足通用 DoD；MVP 闭环可见。

---

### APC-T050 — 实现 Android Timeline：事件列表、编辑、撤销、合并提示

- **所属 Epic**：E06
- **所属 Capability**：C20
- **所属 Story**：S20
- **目标**：实现事件时间线、记录人/来源显示、编辑纠错、软删除撤销、重复提示。
- **前置依赖**：APC-T010, APC-T012, APC-T047
- **输入**：`ARCHITECTURE_FINAL.md` §9.2、§3.2
- **输出**：Timeline feature
- **涉及模块**：android/features/timeline
- **涉及文件**：
  - 新建：`android/src/features/timeline/*`
- **实现要求**：
  - 每条记录显示记录人和来源。
  - 编辑创建 correction，不物理覆盖。
  - 撤销设置 is_deleted。
  - 5 分钟疑似重复喂奶显示软提示，不自动删除。
- **测试要求**：
  - Unit：timeline grouping。
  - Detox：编辑/撤销记录。
- **验收标准**：
  - 用户可查看、编辑、撤销本地/同步事件。
- **DoD**：满足通用 DoD；记录可维护且可审计。

---

### APC-T051 — 实现 Android Alert Center

- **所属 Epic**：E06
- **所属 Capability**：C20
- **所属 Story**：S20
- **目标**：展示告警列表、证据链、确认、反馈。
- **前置依赖**：APC-T031, APC-T046
- **输入**：`ARCHITECTURE_FINAL.md` §14、§3.2
- **输出**：Alert Center feature
- **涉及模块**：android/features/alert_center
- **涉及文件**：
  - 新建：`android/src/features/alert_center/*`
- **实现要求**：
  - 告警详情从 Mac REST 获取，不依赖 FCM payload。
  - ack 调用 server API。
  - feedback 枚举符合架构。
- **测试要求**：
  - Unit：alert view model。
  - Mock API：ack/feedback flow。
- **验收标准**：
  - 用户可确认告警并提交反馈。
  - server 记录 ack_by/ack_at。
- **DoD**：满足通用 DoD；告警人工闭环可用。

---

### APC-T052 — 实现 Android Notification：FCM、Notifee、FullScreenIntent、本地兜底、WorkManager

- **所属 Epic**：E06
- **所属 Capability**：C21 Android 告警与睡眠会话
- **所属 Story**：S21 FCM/Notifee/FullScreenIntent、Sleep Session UI
- **目标**：实现 Android 高优先级告警接收与强提醒能力。
- **前置依赖**：APC-T034, APC-T051
- **输入**：`ARCHITECTURE_FINAL.md` §14.5；`ENGINEERING_DESIGN.md` Android A08/A09
- **输出**：Android notification/background module
- **涉及模块**：android/notification, android/background, native_modules
- **涉及文件**：
  - 新建：`android/src/notification/fcm.ts`, `notifee_channels.ts`, `fullscreen_intent.ts`, `fallback.ts`
  - 新建：`android/src/background/work_manager.ts`
  - 修改：`android/android/app/src/main/AndroidManifest.xml`
- **实现要求**：
  - FCM payload 仅 alert_id/level/type。
  - 收到后回连 Mac 拉详情。
  - red/orange 使用 IMPORTANCE_HIGH、全屏 Intent、持续震动/响铃。
  - 引导 Android 14+ FullScreenIntent 权限、电池/自启白名单。
- **测试要求**：
  - Unit：payload handler。
  - Detox/manual checklist：全屏告警、ack 停止提醒。
- **验收标准**：
  - 模拟 FCM 后可弹出高优先级告警页面。
  - ack 后本地铃声/震动停止。
- **DoD**：满足通用 DoD；手机告警链路可参与 E2E。

---

### APC-T053 — 实现 Android Sleep Session UI 与 ROI 配置

- **所属 Epic**：E06
- **所属 Capability**：C21
- **所属 Story**：S21
- **目标**：实现睡眠会话开始/暂停/结束、snapshot 展示、ROI 配置、影子事件查看。
- **前置依赖**：APC-T037, APC-T038, APC-T039
- **输入**：`ARCHITECTURE_FINAL.md` §3.2、§12.3
- **输出**：Sleep Session feature
- **涉及模块**：android/features/sleep_session
- **涉及文件**：
  - 新建：`android/src/features/sleep_session/*`
- **实现要求**：
  - 只在 active 会话显示分析状态。
  - ROI 手动框定并保存到 server。
  - P0 标注“影子模式，不强提醒”。
- **测试要求**：
  - Unit：session state view model。
  - UI：start/pause/end/ROI save。
- **验收标准**：
  - 用户可从 App 开启会话并配置 ROI。
- **DoD**：满足通用 DoD；摄像头 P0 影子模式具备 UI。

---

## Epic E07 — 端到端验证、部署与硬化

---

### APC-T054 — 实现开发启动脚本、launchd plist 与部署样例

- **所属 Epic**：E07
- **所属 Capability**：C22 DevOps & Fixtures
- **所属 Story**：S22 启动脚本、Mock、Seed、治理命令
- **目标**：提供本地开发与生产 launchd 启动入口。
- **前置依赖**：APC-T003, APC-T036, APC-T044
- **输入**：`ENGINEERING_DESIGN.md` §1.3、§14；`ARCHITECTURE_FINAL.md` §25
- **输出**：run scripts、launchd plist、部署说明
- **涉及模块**：deploy, scripts
- **涉及文件**：
  - 新建：`server/scripts/run_dev.sh`, `run_worker.sh`
  - 新建：`deploy/launchd/com.parenting.server.plist`, `com.parenting.fregata.plist`
  - 新建：`docs/RUNBOOK_DEPLOYMENT.md`
  - 修改：`Makefile`
- **实现要求**：
  - Bootstrap 顺序：infra → alembic → seed → FastAPI/workers。
  - launchd 日志写入 `runtime/logs/`。
  - 不包含真实密钥。
- **测试要求**：
  - Smoke：`make run-dev` 启动 server。
  - Static：plist XML 格式校验。
- **验收标准**：
  - 新机器按 RUNBOOK 可启动 dev 环境。
- **DoD**：满足通用 DoD；部署入口清晰可重复。

---

### APC-T055 — 实现 Dev Fixtures、Fake Services 与 Mock Publishers

- **所属 Epic**：E07
- **所属 Capability**：C22
- **所属 Story**：S22
- **目标**：提供测试夹具、FakeModelClient、FakeFCM、mock camera/mmWave publisher。
- **前置依赖**：APC-T024, APC-T032, APC-T038, APC-T040
- **输入**：`ENGINEERING_DESIGN.md` §12.2
- **输出**：fixtures 与 fake services
- **涉及模块**：tests, server test utils
- **涉及文件**：
  - 新建：`server/tests/fixtures/model_responses/*.json`
  - 新建：`tests/fixtures/radar_frames.jsonl`, `tests/fixtures/rtsp_loop.mp4`
  - 新建：`server/tests/conftest.py`, `server/tests/fakes.py`
  - 新建：`server/scripts/mock_mmwave_publisher.py`
- **实现要求**：
  - CI 禁止真实 LLM/FCM/Camera。
  - 所有 fake 行为可断言。
  - fixtures 不含真实家庭数据。
- **测试要求**：
  - Unit：FakeModelClient/FakeFCM。
  - Integration：mock mmWave publisher 可发 MQTT。
- **验收标准**：
  - 集成测试可在无真实设备环境运行。
- **DoD**：满足通用 DoD；E2E 测试具备稳定测试数据。

---

### APC-T056 — 实现 MVP E2E：离线 Feeding 记录 → 同步 → 派生态回传

- **所属 Epic**：E07
- **所属 Capability**：C23 E2E / Security / Soak
- **所属 Story**：S23 MVP E2E、告警 E2E、安全回归、影子/稳定性验证
- **目标**：验证 P0-M0 最小闭环：Android 离线记录 feeding，恢复网络后同步到 PG，派生态回传 Today。
- **前置依赖**：APC-T017, APC-T047, APC-T048, APC-T049, APC-T055
- **输入**：`ENGINEERING_DESIGN.md` §14 Bootstrap 顺序；§12
- **输出**：跨端 MVP E2E 测试与报告
- **涉及模块**：android, server, sync, events, state_engine
- **涉及文件**：
  - 新建：`tests/e2e/test_mvp_feeding_roundtrip.md` 或自动化脚本
  - 新建：`android/e2e/mvp_feeding.e2e.ts`
  - 修改：`docs/PROJECT_STATE.md`
- **实现要求**：
  - Android 离线写入不依赖 server。
  - 恢复网络后 PowerSync 补传。
  - Server 完成 normalization/state。
  - Today 显示更新。
- **测试要求**：
  - Detox 或半自动 E2E。
  - Server integration log 关联 event_id。
- **验收标准**：
  - 单条 feeding 记录端到端成功。
  - 无重复记录，无丢记录。
- **DoD**：满足通用 DoD；MVP 最小可运行版本达成。

---

### APC-T057 — 实现红色告警 E2E：生成 → 多通道 → 升级 → Ack 停止

- **所属 Epic**：E07
- **所属 Capability**：C23
- **所属 Story**：S23
- **目标**：验证红色告警从 Rule Engine 输出到 Notification 多通道、升级、Android ack 停止全链路。
- **前置依赖**：APC-T021, APC-T034, APC-T052, APC-T055
- **输入**：`ARCHITECTURE_FINAL.md` §14；`ENGINEERING_DESIGN.md` §7.2
- **输出**：Red alert E2E 测试
- **涉及模块**：rule_engine, notification, android notification
- **涉及文件**：
  - 新建：`server/tests/e2e/test_red_alert_delivery.py`
  - 新建：`android/e2e/red_alert_ack.e2e.ts`
- **实现要求**：
  - 使用 FakeFCM/MacSpeaker/CameraSpeaker。
  - 验证 FCM payload 不含详情。
  - 验证 ack 后 cancel。
- **测试要求**：
  - E2E：red alert 生成多条 delivery。
  - E2E：虚拟时间推进触发 60s/90s 升级。
- **验收标准**：
  - 红色告警未 ack 时会升级。
  - ack 后所有通道停止。
- **DoD**：满足通用 DoD；告警必达机制具备回归测试。

---

### APC-T058 — 建立安全回归套件：Dose、Prompt Injection、PII、Canary、审计不可删除

- **所属 Epic**：E07
- **所属 Capability**：C23
- **所属 Story**：S23
- **目标**：整合项目级安全测试，覆盖规则/LLM/隐私/审计关键铁律。
- **前置依赖**：APC-T006, APC-T025, APC-T029, APC-T031
- **输入**：`ENGINEERING_DESIGN.md` §12.1；工厂根目录 `../../../PROJECT_DOSSIER_V5.md` §5.4
- **输出**：Security regression suite
- **涉及模块**：privacy, orchestrator, rule_engine, observability
- **涉及文件**：
  - 新建：`server/tests/security/test_prompt_injection.py`
  - 新建：`server/tests/security/test_audit_immutability.py`
  - 修改：`Makefile`
- **实现要求**：
  - CI 不调用真实模型。
  - 覆盖：剂量绕过、云出站 PII、canary 泄露、audit update/delete。
  - `make security-test` 可单独运行。
- **测试要求**：
  - Security 全部通过。
- **验收标准**：
  - 任何 LLM 自由剂量输出无法通过。
  - PII/canary 无法出站。
  - audit_log 不可删除。
- **DoD**：满足通用 DoD；安全铁律有自动化保护。

---

### APC-T059 — 建立 Shadow/Soak/Harden 验证与发布检查清单

- **所属 Epic**：E07
- **所属 Capability**：C23
- **所属 Story**：S23
- **目标**：实现摄像头/mmWave 7 晚影子模式记录、稳定性 soak 测试与生产前检查清单。
- **前置依赖**：APC-T039, APC-T054, APC-T057, APC-T058
- **输入**：`ENGINEERING_DESIGN.md` §12.1、§12.3；`ARCHITECTURE_FINAL.md` §25.3、§26
- **输出**：Shadow harness、soak 脚本、release checklist
- **涉及模块**：tests, docs, observability
- **涉及文件**：
  - 新建：`tests/shadow/camera_mmwave_shadow_harness.py`
  - 新建：`tests/soak/locustfile.py`
  - 新建：`docs/RELEASE_CHECKLIST_P0.md`
  - 修改：`docs/PROJECT_STATE.md`
- **实现要求**：
  - Shadow 只记录候选与误报反馈，不开强提醒。
  - Soak 目标家庭尺度 1 req/s，记录内存/句柄趋势。
  - Checklist 覆盖 FCM、Mac 声音、摄像头云关闭、ROI、电池白名单、离线补传、备份恢复。
- **测试要求**：
  - Smoke：shadow harness 可跑 mock 数据。
  - Smoke：locustfile 可启动。
- **验收标准**：
  - P0 发布前有可执行检查清单。
  - Shadow 报告可输出误报统计。
- **DoD**：满足通用 DoD；P0 上线硬化路径明确。

---

# 4. MVP 路径

## MVP 定义

最小可运行版本目标：

> 一条 feeding 记录从 Android 离线 Quick Record 写入本地 SQLite，网络恢复后通过 PowerSync 同步到 PostgreSQL，经 Normalization 生成 feeding_log，经 State Engine 更新 DerivedBabyState，并回传 Android Today 首页展示。

## MVP 必须完成任务

按顺序：

1. APC-T001 — 初始化项目目录
2. APC-T002 — FastAPI 应用壳
3. APC-T003 — Docker Compose / Alembic
4. APC-T004 — 核心数据库 Schema
5. APC-T005 — 日志/metrics/health
6. APC-T006 — 审计基础
7. APC-T007 — Auth/RBAC
8. APC-T008 — Auth API / seed_family
9. APC-T009 — ObservationEvent Repository
10. APC-T010 — Events API
11. APC-T011 — PG LISTEN/NOTIFY
12. APC-T012 — PowerSync 适配
13. APC-T013 — Normalization P0
14. APC-T014 — Normalization Worker
15. APC-T015 — State Projection
16. APC-T016 — State API
17. APC-T017 — Event → State 集成链路
18. APC-T045 — Android App 壳
19. APC-T046 — Android Auth
20. APC-T047 — Android Sync / pending_sync
21. APC-T048 — Quick Record P0
22. APC-T049 — Today 首页
23. APC-T055 — Dev Fixtures
24. APC-T056 — MVP E2E

## MVP 验收目标

- Android 断网时可记录 feeding。
- UI 立即显示 pending。
- 恢复网络后事件进入 PostgreSQL。
- Server 自动完成归一化和派生态更新。
- Android Today 显示最新喂奶状态。
- 无丢记录、无重复 event_id。
- 关键操作有审计日志。
- `ruff` / `mypy` / server integration tests / Android basic tests 通过。

---

# 5. 推荐开发顺序

## 阶段 1：地基

1. APC-T001
2. APC-T002
3. APC-T003
4. APC-T004
5. APC-T005
6. APC-T006

## 阶段 2：MVP 服务端记录链路

7. APC-T007
8. APC-T008
9. APC-T009
10. APC-T010
11. APC-T011
12. APC-T012
13. APC-T013
14. APC-T014
15. APC-T015
16. APC-T016
17. APC-T017

## 阶段 3：MVP Android

18. APC-T045
19. APC-T046
20. APC-T047
21. APC-T048
22. APC-T049
23. APC-T055
24. APC-T056

## 阶段 4：规则、安全 AI 与提醒

25. APC-T018
26. APC-T019
27. APC-T020
28. APC-T021
29. APC-T022
30. APC-T023
31. APC-T024
32. APC-T025
33. APC-T026
34. APC-T027
35. APC-T028
36. APC-T029
37. APC-T030
38. APC-T036

## 阶段 5：告警与健康

39. APC-T031
40. APC-T032
41. APC-T033
42. APC-T034
43. APC-T035
44. APC-T051
45. APC-T052
46. APC-T057

## 阶段 6：摄像头、mmWave、媒体与备份

47. APC-T037
48. APC-T038
49. APC-T040
50. APC-T041
51. APC-T042
52. APC-T039
53. APC-T043
54. APC-T044
55. APC-T053

## 阶段 7：部署、硬化与发布准备

56. APC-T054
57. APC-T058
58. APC-T059

---

# 6. 可并行开发部分

## 可并行开发的 Capability

在地基任务 APC-T001～APC-T006 完成后，可并行：

- C04 Auth/RBAC 与 C09 Rule Engine Kernel
- C05 ObservationEvent 与 C11 Model/Privacy/Memory 适配
- C13 Alert Store/API 与 C18 Media/Export
- C19 Android 基础与服务端 Rule Engine
- C16 Camera 与 C17 mmWave，在 Schema 完成后可并行

## 可并行开发的 Story

- S04 Auth 与 S09 Rule Kernel 可并行。
- S07 Normalization 与 S19 Android App 壳可并行。
- S10 各规则域可并行：
  - Medication
  - Triage/Threshold
  - Vaccine
  - Growth
- S14 Notification 通道与 S20 Android Alert Center 可并行，但 E2E 需等两者完成。
- S16 Camera 与 S17 mmWave 可并行。
- S18 Media/Export/Backup 可与 Android 核心页面并行。

## 不建议并行的关键依赖

- 不要在 APC-T004 之前实现 Repository。
- 不要在 APC-T018 之前实现具体 Rule Domain。
- 不要在 APC-T029 之前上线任何医疗/用药 Copilot。
- 不要在 APC-T034 之前做红色告警 E2E。
- 不要在 APC-T047 之前实现 Quick Record 离线写入。

---

# 7. 里程碑规划

## Milestone 1 — P0-M0 工程地基

- **完成能力**：
  - 项目骨架
  - FastAPI 壳
  - Docker Compose
  - Alembic
  - 核心 Schema
  - 日志/metrics/tracing
  - 审计基础
- **对应任务**：
  - APC-T001 ～ APC-T006
- **验收目标**：
  - Server 可启动。
  - DB 可迁移。
  - `/healthz`、`/metrics` 可访问。
  - audit_log 不可删除策略初步建立。

---

## Milestone 2 — P0-M1 服务端记录闭环

- **完成能力**：
  - Auth/RBAC
  - Event Store
  - Events API
  - PowerSync 契约基础
  - PG NOTIFY
  - Normalization
  - Baby State Engine
- **对应任务**：
  - APC-T007 ～ APC-T017
- **验收目标**：
  - 写入 feeding ObservationEvent 后自动生成 feeding_log。
  - DerivedBabyState 自动更新。
  - 事件幂等、软删除、纠错链可测。
  - 服务端记录链路集成测试通过。

---

## Milestone 3 — P0-M2 Android MVP

- **完成能力**：
  - Android app 壳
  - Android Auth
  - op-sqlite + PowerSync
  - Quick Record
  - Today 首页
  - MVP E2E
- **对应任务**：
  - APC-T045 ～ APC-T049
  - APC-T055
  - APC-T056
- **验收目标**：
  - Android 离线 feeding 记录成功。
  - 网络恢复后同步到 Mac。
  - Today 首页展示派生态。
  - MVP E2E 通过。

---

## Milestone 4 — P0-M3 规则、安全 AI 与基础提醒

- **完成能力**：
  - Rule Engine Kernel
  - Medication/Triage/Vaccine/Growth 规则
  - Model Gateway
  - Privacy Adapter
  - Memory Store
  - Orchestrator
  - Dose Interceptor
  - P0 Copilots
  - Scheduler
- **对应任务**：
  - APC-T018 ～ APC-T030
  - APC-T036
- **验收目标**：
  - 规则 golden tests 通过。
  - LLM 剂量输出被拦截并审计。
  - Vaccine/Growth/Medication Basic Copilot 通过 Rule Engine 输出。
  - 晨报/疫苗/补剂提醒可手动触发。

---

## Milestone 5 — P0-M4 告警必达与设备健康

- **完成能力**：
  - Alert API
  - Notification channels
  - 多通道扇出
  - 升级状态机
  - Device Health Monitor
  - Android Alert Center
  - Android FullScreen Notification
- **对应任务**：
  - APC-T031 ～ APC-T035
  - APC-T051 ～ APC-T052
  - APC-T057
- **验收目标**：
  - 红色告警多通道发送。
  - 60s/90s 升级可测。
  - 任一 ack 停止全部提醒。
  - 摄像头等设备离线 60s 内产生灰色告警。
  - 红色告警 E2E 通过。

---

## Milestone 6 — P0-M5 设备、媒体、导出与备份

- **完成能力**：
  - Sleep Session
  - Camera snapshot/ROI
  - mmWave MQTT
  - ESP32C6 固件基础
  - Camera shadow pipeline
  - 加密媒体
  - MD/PDF 导出
  - Backup/Restore
  - Android Sleep Session UI
- **对应任务**：
  - APC-T037 ～ APC-T044
  - APC-T053
- **验收目标**：
  - App 可开启 sleep session 并配置 ROI。
  - dev mock camera/mmWave 数据可入库。
  - 影子模式写 CameraEvent，不强提醒。
  - 媒体加密存储。
  - MD 导出可用。
  - PG dump 可生成，恢复流程有文档。

---

## Milestone 7 — P0 Release Candidate

- **完成能力**：
  - 开发/生产启动脚本
  - Dev fixtures
  - MVP E2E
  - 红警 E2E
  - 安全回归
  - Shadow/Soak
  - P0 发布检查清单
- **对应任务**：
  - APC-T054 ～ APC-T059
- **验收目标**：
  - `make test`、`make security-test`、`make docs-check`、`make governance-check` 通过。
  - MVP E2E 和红警 E2E 通过。
  - 生产前 checklist 可执行。
  - Shadow harness 可运行 mock 数据。
  - 项目具备 P0 家庭试运行条件。
