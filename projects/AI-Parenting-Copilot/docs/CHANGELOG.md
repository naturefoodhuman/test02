<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-31 23:32:00
-->


# CHANGELOG —— AI Parenting Copilot 需求变更与文件影响

> 记录 AI Parenting Copilot 项目级需求变更、任务状态变更和文件影响。工厂根目录 `docs/CHANGELOG.md` 仅作格式参考，不作为本项目状态 SSOT。

## Latest Change Index

- **最新完成任务**：`APC-T008`、`APC-T010`、`APC-T019`、`APC-T031`。
- **当前状态**：用户 Mac DB integration 已 `5 passed`；标准 `make test` 已修复为不受 shell 遗留 DB URL 影响；DB-backed API smoke 可单独通过 `make api-db-smoke-test` 运行；PG worker/Normalization/State DB pipeline 已实现；Worker 链路已通过用户 Mac 复验并解除 `APC-T011/T013/T014/T015/T016/T017` 阻塞；新增 PowerSync smoke target；新增 DB-backed Memory/Orchestrator context，待用户 Mac 复验。
- **下一任务**：继续推进 `APC-T011/T013/T016/T017` 的真实事件 worker/Normalization/State DB pipeline，随后 Android native/RN build 与真实设备验收。

---

## [第 42 轮] 2026-07-31 — DB-backed Memory / Orchestrator context

### 需求变动

- 继续推进 `APC-T026/T027/T028`：新增 PostgreSQL-backed M1-M5 MemorySnapshot、Local RAG 薄适配、Orchestrator DB memory 注入。
- 修复 Logger Copilot 与 Normalization voice parser 不一致问题，复用同一个 deterministic parser。

### 文件影响

新增：

- `server/app/memory/local_rag.py`
- `server/app/memory/sqlalchemy_store.py`

修改：

- `server/app/copilots/logger_copilot.py`
- `server/app/orchestrator/context_builder.py`
- `server/app/orchestrator/orchestrator.py`
- `server/app/orchestrator/api/routes.py`
- `tests/test_memory_store.py`
- `tests/test_logger_copilot.py`
- `tests/integration/test_api_db_runtime.py`
- `docs/TASK_BACKLOG.md`
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`

### 验证

```bash
make lint
make typecheck
python3 -m pytest tests/test_memory_store.py tests/test_logger_copilot.py tests/test_orchestrator.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 148 passed, 8 deselected, 1 warning
```

### 架构影响

- 无架构变更；Memory 优先结构化 PG，M5 仅通过薄 adapter 复用工厂 Local RAG，不复制实现。

---

## [第 41 轮] 2026-07-31 — Worker validation accepted / PowerSync smoke target

### 需求变动

- 用户确认上一轮 worker/DB/API/test 验证通过。
- 同步 `APC-T011/T013/T014/T015/T016/T017` 为 DONE。
- 继续推进 `APC-T012`：新增 PowerSync liveness/config smoke target。

### 文件影响

新增：

- `server/app/sync/service/powersync_probe.py`
- `tests/test_powersync_probe.py`
- `tests/integration_powersync/test_powersync_service.py`

修改：

- `Makefile`
  - 新增 `powersync-smoke-test`。
- `docs/TASK_BACKLOG.md`
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`

### 验证

```bash
make lint
make typecheck
make powersync-smoke-test
# sandbox: 1 passed, 1 skipped
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 146 passed, 8 deselected, 1 warning
```

### 架构影响

- 无架构变更；仅新增 PowerSync 官方服务 liveness/config 验收入口。

---

## [第 40 轮] 2026-07-31 — Live PG worker DB smoke

### 需求变动

- 继续推进 `APC-T011/T014/T017`：新增真实 FastAPI lifespan + `PostgresEventNormalizationWorker` + PostgreSQL `events.changed` NOTIFY 的独立 DB smoke target。

### 文件影响

新增：

- `tests/integration_worker/test_event_normalization_worker.py`

修改：

- `Makefile`
  - 新增 `worker-db-smoke-test`。
- `server/app/state_engine/sqlalchemy_snapshot_repo.py`
  - DB snapshot upsert 持久化 `source_event_count`。
- `docs/TASK_BACKLOG.md`
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`

### 验证

```bash
make lint
make typecheck
make worker-db-smoke-test
# sandbox no DB URL: 1 skipped
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 6 deselected, 1 warning
```

### 架构影响

- 无架构变更；仅新增真实 worker smoke 验收入口。

---

## [第 39 轮] 2026-07-31 — EvidencePolicy activate idempotency

### 需求变动

- 修复用户 Mac `make db-integration-test` 失败：重复运行集成测试或 API smoke 后，同一 medication rule pack 再次 activate 触发 `uq_evidence_policy_version` 唯一键冲突。

### 文件影响

修改：

- `server/app/rule_engine/sqlalchemy_evidence_repo.py`
  - `activate()` 对 exact `(policy_type, region, version)` 幂等返回/复活，不重复 insert。
- `tests/integration/test_db_repository_adapters.py`
  - 增加同一 pack 连续 activate 两次的 regression 断言。
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`

### 验证

```bash
python3 -m ruff check server/app/rule_engine/sqlalchemy_evidence_repo.py tests/integration/test_db_repository_adapters.py
python3 -m mypy server/app
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 5 deselected, 1 warning
make db-integration-test
# sandbox no DB URL: 5 skipped
make api-db-smoke-test
# sandbox no DB URL: 1 skipped
```

### 架构影响

- 无架构变更。
- 保持 Rules Admin / EvidencePolicy repository 边界，仅增强 DB 幂等性。

---

## [第 38 轮] 2026-07-31 — PG worker / DB normalization-state pipeline

### 需求变动

- 继续推进项目完成度：在已通过 DB-backed API smoke 的基础上，实现真实 PostgreSQL 事件变更后的 pending event drain、P0 derived table DB 写入和 DerivedBabyState DB upsert。

### 文件影响

新增：

- `server/app/normalization/sqlalchemy_store.py`
- `server/app/normalization/worker.py`

修改：

- `server/app/main.py`
- `server/app/state_engine/sqlalchemy_snapshot_repo.py`
- `tests/test_normalization_worker.py`
- `tests/integration/test_api_db_runtime.py`
- `docs/TASK_BACKLOG.md`
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`

### 验证

```bash
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 5 deselected, 1 warning
make db-integration-test
# sandbox no DB URL: 5 skipped
make api-db-smoke-test
# sandbox no DB URL: 1 skipped
make lint
make typecheck
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
make docs-check
```

### 架构影响

- 无架构变更；复用既有 `events.changed` PG notify trigger、WorkerRegistry、NormalizationService、BabyStateEngine 与 SQLAlchemy repository 边界。
- `APC-T011/T013/T014/T016/T017` 保持 BLOCKED，等待用户 Mac DB/worker 复验后再按 DoD 解除。

---

## [第 37 轮] 2026-07-31 — DB env test isolation / seed_family DB mode

### 需求变动

- 用户验证 `make db-integration-test` 已通过 `5 passed`，随后发现 `make test` 在同一 shell 里因 `PARENTING_DATABASE__URL` 遗留而误走 DB-backed repositories。
- 继续开发：将 Auth/Event/Rules/Alert DB-backed runtime smoke 验收结果同步到任务状态，并补齐 seed_family DB 持久化入口。

### 文件影响

修改：

- `Makefile`
  - `test` target 显式 unset `PARENTING_DATABASE__URL` / `PARENTING_DATABASE_URL`。
  - `install-dev` 改为 uv-first：`uv pip install --python $(PYTHON) -e ".[dev]"`。
  - 新增 `api-db-smoke-test` target。
- `pyproject.toml`
  - 删除重复 `sqlalchemy[asyncio]`，保留 `sqlalchemy[asyncio]>=2.0`。
- `server/scripts/seed_family.py`
  - 从 in-memory only 升级为 in-memory + DB-backed 双模式。
- `docs/TASK_BACKLOG.md`
  - `APC-T008/T010/T019/T031` 标记为 DONE。
- `docs/PROJECT_STATE.md`
- `docs/DEV_LOG.md`
- `docs/CHANGELOG.md`

新增：

- `tests/conftest.py`
  - 非 `integration` 测试自动隔离 DB 环境变量。
- `tests/test_seed_family.py`
  - 覆盖 seed_family 默认 in-memory 与 `--no-baby`。

### 验证

```bash
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 142 passed, 5 deselected, 1 warning
make lint
make typecheck
make db-integration-test
# sandbox no DB URL: 5 skipped
make api-db-smoke-test
# sandbox no DB URL: 1 skipped
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
make docs-check
```

### 架构影响

- 无架构边界变更。
- DB 覆盖仍通过 `integration` marker；unit/dev tests 保持 in-memory/dev-mock。
- 未新增基础设施或绕过既有 Auth/Repository/Audit/Rule Engine 边界。

---

## [第 36 轮] 2026-07-09 — User-reported bugfixes

### 需求变动

- 处理用户指出的 Makefile/pyproject/feeding projection/voice parser/orchestrator/rule-pack path/request audit 问题。

### 文件影响

- 修改：`Makefile`
- 修改：`pyproject.toml`
- 修改：feeding projection、voice parser、orchestrator、P0 rule copilots、request audit helper
- 修改/新增：相关 regression tests

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
# 140 passed, 5 deselected, 1 warning; security/e2e/shadow/rules checks passed.
```

---

## [第 35 轮] 2026-07-09 — Context handoff consolidation

### 需求变动

- 用户要求在上下文接近上限时更新所有相关文档，保证下一个 Agent 顺利接续。
- 重写项目级 `docs/HANDOFF.md`，并在 `docs/PROJECT_STATE.md` / `docs/DEV_LOG.md` 添加最终交接检查点。

### 文件影响

- 修改：`docs/HANDOFF.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`

### 后续重点

- 下一 Agent 先让用户复验 `make db-integration-test`，预期 `5 passed`。

---

## [第 34 轮] 2026-07-09 — Request-level DB audit wiring + API DB integration fix

### 需求变动

- 修复 API DB runtime integration test transaction teardown / fixture engine 误用问题。
- Auth/Event/Alert/Rules mutating API 在 DB mode 下接入 `audit_log` 写入。
- 修正 TASK_BACKLOG 顶部状态索引与明细状态一致。

### 文件影响

- 新增：`server/app/observability/request_audit.py`
- 修改：Auth/Event/Alert/Rules API routes
- 修改：`tests/integration/test_api_db_runtime.py`
- 修改：项目级维护文档

### 验证

```bash
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped
```

---

## [第 33 轮] 2026-07-09 — DB-backed API runtime integration isolation fix

### 需求变动

- 修复用户 Mac 上 DB-backed API runtime integration test 的 transaction teardown 与 pytest fixture engine 误用问题。

### 文件影响

- 修改：`tests/integration/test_api_db_runtime.py`
- 修改：项目级状态/开发日志

### 验证

```bash
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped
```

---

## [第 32 轮] 2026-07-09 — DB-backed API runtime integration harness

### 需求变动

- 新增 FastAPI DB-backed runtime integration test，覆盖 Auth/Events/Alert/Rules/State API 在 `PARENTING_DATABASE__URL` 存在时使用 SQLAlchemy adapters。

### 文件影响

- 新增：`tests/integration/test_api_db_runtime.py`
- 修改：`server/app/state_engine/api/routes.py`

### 验证

```bash
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped
```

---

## [第 31 轮] 2026-07-09 — Android native skeleton

### 需求变动

- 补齐 Android native skeleton，使手机端应用入口明确位于 `projects/AI-Parenting-Copilot/android/`，native 工程位于 `android/android/`。

### 文件影响

- 新增：`android/android/*`
- 新增：`android/src/native_modules/README.md`
- 新增：`android/e2e/red_alert_ack.e2e.ts`
- 新增：`tests/test_android_native_skeleton.py`

### 验证

```bash
make test
# 137 passed, 4 deselected, 1 warning
```

---

## [第 30 轮] 2026-07-09 — DB-backed runtime repository wiring

### 需求变动

- API runtime 开始支持 DB-backed repository mode：存在 `PARENTING_DATABASE__URL` 时请求级注入 SQLAlchemy session，Auth/Events/Alert/Rules API 使用 DB adapters。

### 文件影响

- 修改：`server/app/main.py`
- 修改：`server/app/auth/api/routes.py`
- 修改：`server/app/events/api/routes.py`
- 修改：`server/app/notification/api/routes.py`
- 修改：`server/app/notification/sqlalchemy_alert_repo.py`
- 修改：`server/app/rule_engine/api/routes.py`

### 验证

```bash
make test
# 134 passed, 4 deselected, 1 warning
```

---

## [第 29 轮] 2026-07-09 — DB integration accepted; core task unblock

### 需求变动

- 用户 Mac `make db-integration-test` 通过 4/4。
- 解除并标记 DONE：`APC-T003`、`APC-T004`、`APC-T006`、`APC-T007`、`APC-T009`、`APC-T018`。

### 文件影响

- 修改：`docs/TASK_BACKLOG.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`

### 验证

```bash
make db-integration-test
# user Mac: 4 passed
```

---

## [第 28 轮] 2026-07-09 — DB integration URL password rendering fix

### 需求变动

- 修复 migration roundtrip integration test 中 SQLAlchemy URL 字符串化隐藏密码为 `***`，导致 asyncpg 认证失败的问题。
- 新增 regression test 确保临时 DB URL 保留真实密码。

### 文件影响

- 修改：`tests/integration/test_db_repository_adapters.py`
- 新增：`tests/test_db_integration_url_rendering.py`
- 修改：项目级状态/开发日志

### 验证

```bash
make test
# 134 passed, 4 deselected, 1 warning
make db-integration-test
# no DB URL: 4 skipped
```

---

## [第 27 轮] 2026-07-09 — DB integration temp database auth fix

### 需求变动

- 修复用户 Mac 上 migration roundtrip integration test 连接 `postgres` maintenance database 时的 `InvalidPasswordError`。
- 临时数据库创建/删除改为通过应用数据库连接执行，避免依赖本地 volume 中 `postgres` database 的单独认证状态。

### 文件影响

- 修改：`tests/integration/test_db_repository_adapters.py`

### 验证

```bash
make test
# 133 passed, 4 deselected, 1 warning
make db-integration-test
# no DB URL: 4 skipped
```

---

## [第 26 轮] 2026-07-09 — Media package tracking fix

### 需求变动

- 修复 `.gitignore` 中 `media/` 递归忽略导致 `server/app/media/*` Python package 未被 Git 跟踪的问题。
- 将 ignore 规则改为仅忽略项目根运行产物 `/media/`，不再忽略 `server/app/media/` 源码目录。
- 补充 `server/app/media/api/__init__.py` 与 `server/app/media/export/__init__.py`。

### 文件影响

- 修改：`.gitignore`
- 新增/纳入跟踪：`server/app/media/*`

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make db-integration-test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
# default tests passed; db-integration-test skipped without DB URL in sandbox
```

---

## [第 25 轮] 2026-07-09 — DB integration test harness

### 需求变动

- 新增 PostgreSQL 集成验收入口 `make db-integration-test`。
- 默认 `make test` 排除 integration marker，避免无 DB 环境误跑。

### 文件影响

- 新增：`tests/integration/test_db_repository_adapters.py`
- 修改：`Makefile`、`pyproject.toml`
- 修改：项目级维护文档

### 验证

```bash
make test
# 133 passed, 2 deselected, 1 warning
make db-integration-test
# no DB URL: 2 skipped
```

---

## [第 24 轮] 2026-07-09 — Additional DB-backed repository adapter skeletons

### 需求变动

- 继续减少 DB 持久化 BLOCKED 任务的剩余工作。
- 新增 State/EvidencePolicy/Media/Delivery/SleepSession SQLAlchemy adapters；状态不改为 DONE，等待真实 PostgreSQL 集成验收。

### 文件影响

- 新增：`server/app/state_engine/sqlalchemy_snapshot_repo.py`
- 新增：`server/app/rule_engine/sqlalchemy_evidence_repo.py`
- 新增：`server/app/media/sqlalchemy_media_repo.py`
- 新增：`server/app/notification/sqlalchemy_delivery_repo.py`
- 新增：`server/app/camera/sqlalchemy_sleep_session_repo.py`
- 新增：`tests/test_more_db_repository_adapters.py`

### 验证

```bash
make docs-check && make lint && make typecheck && make test
# 133 passed, 1 warning
```

---

## [第 23 轮] 2026-07-09 — DB-backed repository adapter skeletons

### 需求变动

- 继续减少 DB 持久化 BLOCKED 任务的剩余工作。
- 新增 Auth/Event/Alert SQLAlchemy repository adapters；状态不改为 DONE，等待真实 PostgreSQL 集成验收。

### 文件影响

- 新增：`server/app/auth/infra/sqlalchemy_repository.py`
- 新增：`server/app/events/infra/sqlalchemy_repository.py`
- 新增：`server/app/notification/sqlalchemy_alert_repo.py`
- 新增：`tests/test_db_repository_adapters.py`

### 验证

```bash
make docs-check && make lint && make typecheck && make test
# 130 passed, 1 warning
```

---

## [第 22 轮] 2026-07-09 — APC-T056 checklist / APC-T059 Shadow-Soak-Harden

### 需求变动

- 完成 MVP feeding semi-automated checklist、Detox placeholder、Shadow harness、soak locustfile、P0 release checklist。

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
# 127 passed, 1 warning
```

---

## [第 21 轮] 2026-07-09 — APC-T011/T012/T019 dev 逻辑完成，集成验收 BLOCKED

### 需求变动

- 完成 PG notify trigger migration/static parser、PowerSync contract validator/soft conflict hint、Rules Admin validate/activate dev API。

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make rules-validate
# 125 passed, 1 warning
```

---

## [第 20 轮] 2026-07-09 — APC-T013~T017 Normalization / State Engine dev chain

### 需求变动

- 完成 Normalization parsers/service、dedup/correction helpers、Baby State projections、State API dev 与 event→normalization→state integration test。

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make rules-validate
# 120 passed, 1 warning
```

---

## [第 19 轮] 2026-07-09 — APC-T049/T050/T051/T052/T053 Android feature static logic

### 需求变动

- 继续并行开发不依赖 Android native toolchain 的代码。
- 完成 Today、Timeline、Alert Center、Notification、Sleep Session feature view models/flows。

### 验证

```bash
make docs-check && make lint && make typecheck && make test
# 114 passed, 1 warning
```

---

## [第 18 轮] 2026-07-09 — APC-T045/T046/T047/T048 Android skeleton/static logic

### 需求变动

- 继续并行开发不依赖 Android native toolchain 的代码。
- 完成 Android-only RN source skeleton、Auth/session TS flow、sync schema/local pending store、Quick Record candidate builder。

### 文件影响

新增/修改：

- `android/package.json`, `android/tsconfig.json`, `android/README.md`
- `android/src/App.tsx`, `api`, `navigation`, `theme`, `state`, `features/auth`, `sync`, `features/quick_record`
- `tests/test_android_skeleton.py`
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check && make lint && make typecheck && make test
# 109 passed, 1 warning
```

---

## [第 17 轮] 2026-07-09 — APC-T054/T055/T057/T058 dev 逻辑完成，验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实设备/DB/Android 的代码。
- 完成 DevOps run scripts/launchd/runbook、fixtures/fakes/mock publisher、fake red alert E2E、安全回归套件。

### 文件影响

新增/修改：

- `server/scripts/run_dev.sh`, `run_worker.sh`, `mock_mmwave_publisher.py`
- `deploy/launchd/com.parenting.server.plist`, `com.parenting.fregata.plist`
- `docs/RUNBOOK_DEPLOYMENT.md`
- `tests/fakes.py`, `tests/security/*`, `tests/e2e/*`, fixtures
- Makefile security/e2e targets
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make rules-validate
# 104 passed, 1 warning; security-test 5 passed; e2e-fake-test 1 passed.
```

---

## [第 16 轮] 2026-07-09 — APC-T041 / APC-T044 dev 逻辑完成，验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实硬件/NAS 的代码。
- 完成 ESP32C6 firmware skeleton 与 backup dry-run/runbook。

### 文件影响

新增/修改：

- `firmware/esp32c6/*`
- `server/app/backup/*`
- `deploy/launchd/com.parenting.backup.plist`
- `docs/RUNBOOK_BACKUP_RESTORE.md`
- backup/firmware tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check && make lint && make typecheck && make test && make rules-validate
# 98 passed, 1 warning; rule packs validated.
```

---

## [第 15 轮] 2026-07-09 — APC-T042 / APC-T043 dev 逻辑完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB 的代码。
- 完成 media encrypted storage/thumbnail/dev API 与 export markdown/pdf placeholder。

### 文件影响

新增/修改：

- `server/app/media/*`
- `server/app/export/*`
- `server/app/main.py`
- media/export tests
- `pyproject.toml` 新增 cryptography/Pillow 依赖
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 117 source files
make test
# 95 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 14 轮] 2026-07-09 — APC-T039 / APC-T040 dev 逻辑完成，集成验收 BLOCKED

### 需求变动

- 继续并行开发不依赖真实 DB/MQTT/VLM 的代码。
- 完成 camera shadow fusion/VLM dispatcher 与 mmWave parser/mapper/subscriber skeleton。

### 文件影响

新增/修改：

- `server/app/mmwave/*`
- `server/app/camera/clip_recorder.py`
- `server/app/camera/fusion.py`
- `server/app/camera/vlm_dispatcher.py`
- `tests/fixtures/radar_frames.jsonl`
- camera shadow / mmWave tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 109 source files
make test
# 90 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 13 轮] 2026-07-09 — uv-first 依赖修复 + APC-T037/T038 dev 逻辑

### 需求变动

- 用户确认不能直接依赖 pip，应使用 uv pip；`ensure-dev-deps` 改为 uv-first。
- 完成 Sleep Session state machine/dev API 与 Camera mock snapshot/adapters。

### 文件影响

新增/修改：

- `server/scripts/ensure_dev_deps.py`
- `server/app/camera/*`
- `config/devices.yaml`
- `server/app/main.py`
- camera/sleep tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 102 source files
make test
# 83 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## [第 12 轮] 2026-07-09 — pipless venv 修复 + APC-T034/T035/T036 dev 逻辑

### 需求变动

- 修复用户验收中 `.venv/bin/python3: No module named pip` 导致 ensure-dev-deps 失败的问题。
- 完成 Escalation、Device Health、Scheduler dev 纯逻辑。

### 文件影响

新增/修改：

- `server/scripts/ensure_dev_deps.py`
- `server/app/notification/escalation.py`
- `server/app/health/monitor.py`
- `server/app/scheduler/*`
- `server/app/health/api.py`
- `server/app/notification/channels/fake.py`
- escalation/device-health/scheduler tests
- 项目级维护文档与根目录 CHANGELOG

### 验证

```bash
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 95 source files
make test
# 78 passed, 1 warning
make rules-validate
# rule packs validated
```

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
