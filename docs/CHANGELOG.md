<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-01 11:52:00
-->

# CHANGELOG —— 需求增删改 + 变动说明

> 老板每轮提出的"新增 / 删除 / 改动"需求，以及由此产生的文件变动，都记在这里。
> 格式：每轮一节，列出【需求变动】和【文件影响】。

## Latest Change Index

- **当前状态 SSOT**：`docs/PROJECT_STATE.md`；AI Parenting Copilot 项目内状态见 `projects/AI-Parenting-Copilot/docs/PROJECT_STATE.md`。
- **最新完成模块**：AI Parenting Copilot APC-T008/T010/T019/T031 DB-backed API runtime hardening；`make test` DB env isolation；seed_family DB mode；PG worker/Normalization/State DB pipeline；EvidencePolicy activate idempotency；live worker DB smoke target；PowerSync validation accepted；DB-backed Memory/Orchestrator context；Dose Interceptor DB audit；Notification adapters / DB delivery dispatch / cancel receipts；Android native critical alert fallback；Android Gradle bootstrap；Android secure session/native pending event store；Android Quick Record native offline write；System health real probes；FastAPI local API runbook/smoke targets；Scheduler API。
- **当前 Network 测试基线**：358 passed, 3 skipped, 44 warnings。
- **当前 AI Parenting Copilot 测试基线**：`PARENTING_DATABASE__URL=... make test` → `159 passed, 8 deselected, 1 warning`；用户 Mac `make db-integration-test` → `5 passed, 1 warning`。
- **历史条目说明**：早期条目保留为审计历史，可能引用已归档或已删除文件；不要把历史条目当作当前状态。

---

## [第 149 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot 验收状态同步**：用户确认 FastAPI health smoke 真实环境通过，`APC-T035` 标记为 DONE。
- **AI Parenting Copilot Scheduler 推进**：新增 Scheduler API job list/trigger/trigger-all 与 audit，推进 `APC-T036`。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/scheduler/api/routes.py`
- 新增：`projects/AI-Parenting-Copilot/tests/test_scheduler_api.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/main.py`
- 修改：project docs / root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
python3 -m pytest tests/test_scheduler_api.py tests/test_scheduler_jobs.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 159 passed, 8 deselected, 1 warning
```

---

## [第 148 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot 运维说明修复**：用户指出 curl 8000 失败是因为没有说明 FastAPI 服务需先启动；新增本地 API 启动 runbook 与 smoke targets。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/docs/RUNBOOK_LOCAL_API.md`
- 新增：`projects/AI-Parenting-Copilot/server/scripts/api_health_smoke.py`
- 新增：`projects/AI-Parenting-Copilot/server/scripts/api_server_smoke.py`
- 修改：`projects/AI-Parenting-Copilot/Makefile`
- 修改：`projects/AI-Parenting-Copilot/README.md`
- 修改：`projects/AI-Parenting-Copilot/server/scripts/run_dev.sh`
- 修改：project docs / root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
make api-server-smoke-test
```

---

## [第 147 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot Health Monitor 推进**：新增 DB/TCP/HTTP/PowerSync real health probes，并暴露 system health check API，推进 `APC-T035`。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/health/probes/*`
- 新增：`projects/AI-Parenting-Copilot/tests/test_health_probes.py`
- 新增：`projects/AI-Parenting-Copilot/tests/test_health_api_probes.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/health/api.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/main.py`
- 修改：project docs / root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 157 passed, 8 deselected, 1 warning
```

---

## [第 146 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot Android 离线记录推进**：新增 native Quick Record local offline write 与 Pending Sync status screen，推进 `APC-T047/T048`。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt`
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/PendingEventsActivity.kt`
- 修改：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/MainActivity.kt`
- 修改：`projects/AI-Parenting-Copilot/android/android/app/src/main/AndroidManifest.xml`
- 修改：`projects/AI-Parenting-Copilot/tests/test_android_native_skeleton.py`
- 修改：project docs / root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 154 passed, 8 deselected, 1 warning
```

---

## [第 145 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot Android 验收状态同步**：用户确认 `./gradlew assembleDebug` 成功；项目级 `APC-T045` 标记为 DONE。
- **AI Parenting Copilot Android 继续开发**：新增 Android Keystore secure session store、native SQLite pending event store 与 TS bridge contracts，推进 `APC-T046/T047`。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/SecureSessionStore.kt`
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/LocalObservationEvent.kt`
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/LocalEventStore.kt`
- 新增：`projects/AI-Parenting-Copilot/android/src/features/auth/native_secure_session.ts`
- 新增：`projects/AI-Parenting-Copilot/android/src/sync/native_sqlite_bridge.ts`
- 修改：Android static tests/project docs/root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 154 passed, 8 deselected, 1 warning
```

---

## [第 144 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot Android build 修复**：用户执行 `cd android/android && ./gradlew assembleDebug` 失败，原因是 `gradlew` 缺失；新增 Android Gradle bootstrap wrapper 与 `make android-native-build`。
- **AI Parenting Copilot 验收状态同步**：用户确认 notification dispatch/cancel 所在 API/test 复验通过；项目级 `APC-T032/T033/T034` 标记为 DONE。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/android/android/gradlew`
- 新增：`projects/AI-Parenting-Copilot/android/android/gradlew.bat`
- 新增：`projects/AI-Parenting-Copilot/android/android/gradle/wrapper/gradle-wrapper.properties`
- 修改：Android README/package、Makefile、gitignore、Android native skeleton tests、project docs、root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 152 passed, 8 deselected, 1 warning
```

---

## [第 143 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot Android 告警推进**：新增 Android native critical alert full-screen fallback skeleton（trigger-only payload、Activity、Receiver、NotificationHelper、TS bridge）。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/AlertPayload.kt`
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/CriticalAlertActivity.kt`
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/AlertActionReceiver.kt`
- 新增：`projects/AI-Parenting-Copilot/android/android/app/src/main/java/com/aiparentingcopilot/NotificationHelper.kt`
- 新增：`projects/AI-Parenting-Copilot/android/src/notification/native_bridge.ts`
- 修改：Android manifest/application/static tests/project docs

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 152 passed, 8 deselected, 1 warning
```

---

## [第 142 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot 验收状态同步**：用户确认 Dose Interceptor DB audit 所在本地复验通过；项目级 `APC-T029` 标记为 DONE。
- **AI Parenting Copilot 通知升级推进**：新增 ack 后 channel cancel，持久化 cancelled delivery receipts，并新增 deliveries 查询 API。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/server/app/notification/orchestrator.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/notification/api/routes.py`
- 修改：notification tests / API DB smoke / project docs / root CHANGELOG

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 151 passed, 8 deselected, 1 warning
```

---

## [第 141 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot 通知链路推进**：新增 safe FCM/Mac/App/Camera notification adapters、alert dispatch API 与 DB `alert_delivery` 持久化，推进 `APC-T032/T033`。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/notification/channels/fcm.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/notification/channels/mac_speaker.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/notification/channels/app_fullscreen.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/notification/channels/camera_speaker.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/notification/channel_factory.py`
- 修改：notification API/orchestrator/main/tests/project docs

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 150 passed, 8 deselected, 1 warning
```

---

## [第 140 轮] 2026-08-01

### 需求变动
- **AI Parenting Copilot 状态同步**：用户确认 DB-backed Memory/Orchestrator 复验通过；项目级 `APC-T020/T021/T026/T027/T028` 标记为 DONE。
- **AI Parenting Copilot 安全推进**：新增 `SQLAlchemyAuditSink`，Dose Interceptor 的 `dose_intercept` 可写真实 `audit_log`，并扩展 API DB smoke 覆盖。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/observability/sqlalchemy_audit_sink.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/orchestrator/api/routes.py`
- 修改：`projects/AI-Parenting-Copilot/tests/integration/test_api_db_runtime.py`
- 修改：项目级维护文档与根 `docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
python3 -m ruff check server/app/observability/sqlalchemy_audit_sink.py server/app/orchestrator/api/routes.py tests/integration/test_api_db_runtime.py
python3 -m mypy server/app
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 148 passed, 8 deselected, 1 warning
```

---

## [第 139 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 验收状态同步**：用户确认 `make powersync-smoke-test` 等上一轮验证全部通过；项目级 `APC-T012` 标记为 DONE。

### 文件影响
- 修改：项目级 `TASK_BACKLOG` / `PROJECT_STATE` / `DEV_LOG` / `CHANGELOG` / `HANDOFF`
- 修改：`docs/CHANGELOG.md`

---

## [第 138 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 继续开发**：新增 SQLAlchemy-backed M1-M5 MemorySnapshot、Local RAG 薄适配、Orchestrator DB memory injection，并让 Logger Copilot 复用 Normalization voice parser。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/memory/local_rag.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/memory/sqlalchemy_store.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/copilots/logger_copilot.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/orchestrator/context_builder.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/orchestrator/orchestrator.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/orchestrator/api/routes.py`
- 修改：`projects/AI-Parenting-Copilot/tests/test_memory_store.py`
- 修改：`projects/AI-Parenting-Copilot/tests/test_logger_copilot.py`
- 修改：`projects/AI-Parenting-Copilot/tests/integration/test_api_db_runtime.py`
- 修改：项目级维护文档与根 `docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
python3 -m pytest tests/test_memory_store.py tests/test_logger_copilot.py tests/test_orchestrator.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 148 passed, 8 deselected, 1 warning
```

---

## [第 137 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 验收通过后继续推进**：用户确认 worker/DB/API/test 验证通过；项目级 `APC-T011/T013/T014/T015/T016/T017` 已同步 DONE。
- **AI Parenting Copilot PowerSync 复验入口**：新增 PowerSync liveness/config probe 与 `make powersync-smoke-test`，用于推进 `APC-T012`。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/sync/service/powersync_probe.py`
- 新增：`projects/AI-Parenting-Copilot/tests/test_powersync_probe.py`
- 新增：`projects/AI-Parenting-Copilot/tests/integration_powersync/test_powersync_service.py`
- 修改：`projects/AI-Parenting-Copilot/Makefile`
- 修改：项目级 `TASK_BACKLOG` / `PROJECT_STATE` / `DEV_LOG` / `CHANGELOG` / `HANDOFF`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
make powersync-smoke-test
# sandbox: 1 passed, 1 skipped
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 146 passed, 8 deselected, 1 warning
```

---

## [第 136 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 继续开发**：新增 `make worker-db-smoke-test`，用于用户 Mac 验证真实 FastAPI lifespan + `PostgresEventNormalizationWorker` + PostgreSQL `events.changed` NOTIFY 能自动完成 event→normalization→state。
- **AI Parenting Copilot 状态持久化修复**：`SQLAlchemyStateSnapshotRepository.upsert()` 现在将 `source_event_count` 写入 snapshot JSON，避免 DB API 读取时丢失来源事件数。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/Makefile`
- 修改：`projects/AI-Parenting-Copilot/server/app/state_engine/sqlalchemy_snapshot_repo.py`
- 新增：`projects/AI-Parenting-Copilot/tests/integration_worker/test_event_normalization_worker.py`
- 修改：项目级 `TASK_BACKLOG` / `PROJECT_STATE` / `DEV_LOG` / `CHANGELOG` / `HANDOFF`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
make lint
make typecheck
make worker-db-smoke-test
# sandbox no DB URL: 1 skipped
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 6 deselected, 1 warning
```

---

## [第 135 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 验收修复**：修复用户 Mac `make db-integration-test` 中重复激活同一 EvidencePolicy rule pack 导致 `uq_evidence_policy_version` 唯一键冲突的问题。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/server/app/rule_engine/sqlalchemy_evidence_repo.py`
- 修改：`projects/AI-Parenting-Copilot/tests/integration/test_db_repository_adapters.py`
- 修改：项目级 `PROJECT_STATE` / `DEV_LOG` / `CHANGELOG` / `HANDOFF`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
python3 -m ruff check server/app/rule_engine/sqlalchemy_evidence_repo.py tests/integration/test_db_repository_adapters.py
python3 -m mypy server/app
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 5 deselected, 1 warning
make db-integration-test
# sandbox no DB URL: 5 skipped
make api-db-smoke-test
# sandbox no DB URL: 1 skipped
```

---

## [第 134 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 继续开发**：实现 PostgreSQL `events.changed` LISTEN/NOTIFY worker、pending ObservationEvent drain、P0 derived tables SQLAlchemy upsert/read、DerivedBabyState PostgreSQL `ON CONFLICT` upsert，并扩展 DB-backed API integration smoke。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/normalization/sqlalchemy_store.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/normalization/worker.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/main.py`
- 修改：`projects/AI-Parenting-Copilot/server/app/state_engine/sqlalchemy_snapshot_repo.py`
- 修改：`projects/AI-Parenting-Copilot/tests/test_normalization_worker.py`
- 修改：`projects/AI-Parenting-Copilot/tests/integration/test_api_db_runtime.py`
- 修改：项目级 `TASK_BACKLOG` / `PROJECT_STATE` / `DEV_LOG` / `CHANGELOG` / `HANDOFF`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 5 deselected, 1 warning
make db-integration-test
# sandbox no DB URL: 5 skipped
make api-db-smoke-test
# sandbox no DB URL: 1 skipped
make lint && make typecheck && make security-test && make e2e-fake-test && make shadow-test && make rules-validate && make docs-check
```

---

## [第 133 轮] 2026-07-31

### 需求变动
- **AI Parenting Copilot 验收修复与继续开发**：用户确认 `make db-integration-test` 已在 Mac/PostgreSQL 环境通过 `5 passed`；修复随后 `make test` 因 shell 遗留 `PARENTING_DATABASE__URL` 误切 DB repo 的失败。
- **AI Parenting Copilot DB runtime 完成度推进**：新增 `make api-db-smoke-test`；`seed_family.py` 支持 in-memory 与 DB-backed 持久化双模式；同步 `APC-T008/T010/T019/T031` 为 DONE。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/Makefile`
- 修改：`projects/AI-Parenting-Copilot/pyproject.toml`
- 修改：`projects/AI-Parenting-Copilot/server/scripts/seed_family.py`
- 新增：`projects/AI-Parenting-Copilot/tests/conftest.py`
- 新增：`projects/AI-Parenting-Copilot/tests/test_seed_family.py`
- 修改：`projects/AI-Parenting-Copilot/docs/TASK_BACKLOG.md`
- 修改：`projects/AI-Parenting-Copilot/docs/PROJECT_STATE.md`
- 修改：`projects/AI-Parenting-Copilot/docs/DEV_LOG.md`
- 修改：`projects/AI-Parenting-Copilot/docs/CHANGELOG.md`
- 修改：`projects/AI-Parenting-Copilot/docs/HANDOFF.md`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
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

---

## [第 132 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot bugfix**：修复用户指出的 Makefile uv usage、SQLAlchemy asyncio dependency、feeding 24h projection、voice parser robustness、Orchestrator duplicate request、rule-pack relative path/import-time I/O、request audit helper 问题。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
# 140 passed, 5 deselected, 1 warning; supporting checks passed.
```

---

## [第 131 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 交接收敛**：用户要求在上下文上限前更新相关文档；已重写项目级 `docs/HANDOFF.md` 并补充 `PROJECT_STATE` / `DEV_LOG` / `CHANGELOG` 最新接续信息。

### 后续重点
- 下一 Agent 应先复验用户 Mac `make db-integration-test`，预期 `5 passed`。

---

## [第 130 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 验收修复与增强**：修复 API DB runtime integration transaction isolation；新增 request-level DB audit helper，使 Auth/Event/Alert/Rules mutating API 在 DB mode 下写入 audit_log。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL in sandbox: 5 skipped; user Mac should run real 5 tests
```

---

## [第 129 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 验收修复**：修复 DB-backed API runtime integration test 中 transaction teardown 与 pytest fixture engine 误用问题；改为显式使用 AsyncEngine fixture、独立 session seed baby，并在测试后清理 family 相关数据。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL in sandbox: 5 skipped; user Mac should run real 5 tests
```

---

## [第 128 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 集成验收增强**：新增 DB-backed FastAPI runtime integration test，覆盖 Auth/Events/Alert/Rules/State API 在真实 DB session 下的 smoke flow。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL in sandbox: 5 skipped; with PARENTING_DATABASE__URL on Mac should run 5 real integration tests
```

---

## [第 127 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot Android skeleton**：补齐 `projects/AI-Parenting-Copilot/android/android/` native Android project skeleton，明确手机端应用入口。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 137 passed, 4 deselected, 1 warning
```

---

## [第 126 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：API runtime 增加 DB-backed repository mode，按请求注入 SQLAlchemy session；Auth/Events/Alert/Rules API 可在 DB URL 存在时使用 SQLAlchemy adapters。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 134 passed, 4 deselected, 1 warning
```

---

## [第 125 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 验收通过**：用户 Mac `make db-integration-test` 通过 4/4。
- **任务状态解除**：`APC-T003/T004/T006/T007/T009/T018` 从 BLOCKED 标记为 DONE。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make db-integration-test
# user Mac: 4 passed
```

---

## [第 124 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 验收修复**：修复 `make db-integration-test` 中 migration roundtrip URL 使用 SQLAlchemy 默认 masked password (`***`) 导致 asyncpg 认证失败的问题，改用 `render_as_string(hide_password=False)`。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 134 passed, 4 deselected, 1 warning
make db-integration-test
# no DB URL in sandbox: 4 skipped
```

---

## [第 123 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 验收修复**：修复 `make db-integration-test` 中 migration roundtrip test 连接 `postgres` maintenance database 的本地认证兼容问题，改为使用已验证的应用数据库连接创建/删除临时 database。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 133 passed, 4 deselected, 1 warning
make db-integration-test
# no DB URL in sandbox: 4 skipped
```

---

## [第 122 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 验收问题修复**：修复项目 `.gitignore` 中 `media/` 递归忽略导致 `server/app/media` 源码包未提交的问题；改为仅忽略根级运行产物 `/media/`。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/.gitignore`
- 新增跟踪：`projects/AI-Parenting-Copilot/server/app/media/*`

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make db-integration-test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
```

---

## [第 121 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 集成验收增强**：新增 `make db-integration-test`，用于真实 PostgreSQL transaction 级验证 DB repository adapters、EvidencePolicy activation 与 audit_log immutability。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make test
# 133 passed, 2 deselected, 1 warning
make db-integration-test
# no DB URL: 2 skipped; with PARENTING_DATABASE__URL on Mac should run real integration tests
```

---

## [第 120 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：新增 State/EvidencePolicy/Media/Delivery/SleepSession SQLAlchemy repository adapters，为后续解除 DB 持久化 BLOCKED 做准备。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# 133 passed, 1 warning.
```

---

## [第 119 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：新增 Auth/Event/Alert SQLAlchemy repository adapters，为后续解除 DB 持久化 BLOCKED 做准备。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# 130 passed, 1 warning.
```

---

## [第 118 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 APC-T056 MVP feeding semi-automated checklist 与 APC-T059 Shadow/Soak/Harden harness/checklist。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
# 127 passed, 1 warning; security/e2e/shadow/rules checks passed.
```

---

## [第 117 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 APC-T011 PG notify trigger/parser、APC-T012 sync contract validator、APC-T019 Rules Admin dev API。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# 125 passed, 1 warning; rule packs validated.
```

---

## [第 116 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 APC-T013~T017 Normalization / Baby State Engine dev chain。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# 120 passed, 1 warning; rule packs validated.
```

---

## [第 115 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 Android Today/Timeline/Alert Center/Notification/Sleep Session TS view models 与 flows。

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# 114 passed, 1 warning.
```

---

## [第 114 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 Android-only RN source skeleton、Auth/session TS flow、sync schema/local pending store、Quick Record candidate builder。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/android/*`
- 新增：Android static tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# 109 passed, 1 warning.
```

---

## [第 113 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 DevOps run scripts/launchd/runbook、fixtures/fakes/mock publisher、fake red alert E2E、安全回归套件。

### 文件影响
- 新增：DevOps scripts/plists/runbook
- 新增：fixtures/fakes/mock publisher
- 新增：security/e2e tests
- 修改：Makefile 与项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make rules-validate
# 104 passed, 1 warning; security-test 5 passed; e2e-fake-test 1 passed.
```

---

## [第 112 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T041` ESP32C6 firmware skeleton 与 `APC-T044` backup dry-run/runbook。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/firmware/esp32c6/*`
- 新增：`projects/AI-Parenting-Copilot/server/app/backup/*`
- 新增：backup runbook / launchd plist / tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# 98 passed, 1 warning; rule packs validated.
```

---

## [第 111 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T042` Media encrypted storage/thumbnail/dev API 与 `APC-T043` Export MD/PDF placeholder。
- **验收状态**：真实 DB media_asset、audit_log、State Engine/event query 与下载授权仍待后续验收，因此相关任务标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/media/*`
- 新增：`projects/AI-Parenting-Copilot/server/app/export/*`
- 修改：`server/app/main.py`、`pyproject.toml`
- 新增：media/export tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 95 passed, 1 warning; rule packs validated.
```

---

## [第 110 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T039` camera shadow fusion/VLM dispatcher 与 `APC-T040` mmWave parser/mapper/subscriber skeleton。
- **验收状态**：真实 MQTT、DB sensor_event/camera_event、VLM/ModelGateway 和媒体 clip 写入仍待后续验收，因此相关任务标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/mmwave/*`
- 新增：camera shadow modules 与 mmWave/camera shadow tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 90 passed, 1 warning; rule packs validated.
```

---

## [第 109 轮] 2026-07-09

### 需求变动
- **验收问题修复**：用户明确 venv 依赖安装需使用 `uv pip`；AI Parenting Copilot `ensure-dev-deps` 改为 uv-first，只有 uv 不存在时才 fallback 到 pip/ensurepip。
- **并行推进**：完成 `APC-T037` Sleep Session dev API 与 `APC-T038` Camera mock snapshot/adapters。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/server/scripts/ensure_dev_deps.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/camera/*`
- 新增：`projects/AI-Parenting-Copilot/config/devices.yaml`
- 新增：camera/sleep tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 83 passed, 1 warning; rule packs validated.
```

---

## [第 108 轮] 2026-07-09

### 需求变动
- **验收问题修复**：`ensure-dev-deps` 支持无 pip 的 uv venv，使用 ensurepip 或 uv pip fallback 安装项目 dev 依赖。
- **并行推进**：完成 `APC-T034` Escalation、`APC-T035` Device Health Monitor、`APC-T036` Scheduler jobs dev 逻辑。

### 文件影响
- 修改：`projects/AI-Parenting-Copilot/server/scripts/ensure_dev_deps.py`
- 新增/修改：`notification/escalation.py`、`health/monitor.py`、`scheduler/*`
- 新增：相关测试
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 78 passed, 1 warning; rule packs validated.
```

---

## [第 107 轮] 2026-07-09

### 需求变动
- **验收问题修复**：为 AI Parenting Copilot 增加 `ensure-dev-deps`，Makefile 自动安装当前 venv 缺失的 alembic/structlog/python-ulid/pytest-asyncio/ruff/mypy 等依赖。
- **并行推进**：完成 `APC-T031` Alert dev repo/API、`APC-T032` Notification fake channels、`APC-T033` Notification fan-out 纯逻辑。

### 文件影响
- 新增/修改：`projects/AI-Parenting-Copilot/server/scripts/ensure_dev_deps.py`、`Makefile`、`pyproject.toml`
- 新增：`projects/AI-Parenting-Copilot/server/app/notification/*`
- 新增：`projects/AI-Parenting-Copilot/config/notification.yaml`
- 新增：alert/notification tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 72 passed, 1 warning; rule packs validated.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 106 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T030` P0 Copilot wrappers 纯逻辑与测试。
- **验收状态**：前置 Rule/Orchestrator/Dose/Memory 与真实 DB/audit 集成仍待后续验收，因此 T030 标记 BLOCKED。

### 文件影响
- 新增：P0 Copilot wrapper modules
- 修改：`server/app/orchestrator/orchestrator.py`
- 新增：`tests/test_p0_copilots.py`
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 67 passed, 1 warning; rule packs validated.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 105 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T026` Memory snapshot、`APC-T027` Logger Copilot、`APC-T028` Orchestrator dev API 与 `APC-T029` Dose Interceptor 纯逻辑。
- **验收状态**：State Engine、真实 Memory/RAG、DB-backed audit 与完整编排接入仍待后续验收，因此相关任务标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/memory/*`
- 新增：`projects/AI-Parenting-Copilot/server/app/copilots/*`
- 新增：`projects/AI-Parenting-Copilot/server/app/orchestrator/*`
- 新增：相关 tests
- 修改：`server/app/main.py` 与项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 62 passed, 1 warning; rule packs validated.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 104 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T022` Vaccine Planner 与 `APC-T023` Growth Rule Domain 的纯逻辑与测试。
- **验收状态**：前置 Rule Engine DB/audit、生产规则审查与完整 WHO 表仍待后续验收，因此相关任务标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/rule_engine/domains/vaccine.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/rule_engine/domains/growth.py`
- 新增：vaccine/growth rule packs 与 golden tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 53 passed, 1 warning; rule packs validated.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 103 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T018` Rule Engine kernel、`APC-T020` Medication rules、`APC-T021` Triage/Threshold rules 的纯逻辑与测试。
- **验收状态**：EvidencePolicy DB/audit、State Engine 输入与真实告警联动仍待后续验收，因此相关任务标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/rule_engine/*`
- 新增：`projects/AI-Parenting-Copilot/config/rules/*`
- 新增：`projects/AI-Parenting-Copilot/tests/golden/rules/*`
- 新增：rule engine / medication / triage / threshold tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test && make rules-validate
# Project docs-check passed; ruff passed; mypy passed; 49 passed, 1 warning; rule packs validated.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 102 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T009` ObservationEvent 契约/in-memory repository 与 `APC-T010` Events API dev 代码。
- **验收状态**：真实 DB repository、PowerSync 写入契约与 audit_log 持久化仍依赖 PostgreSQL，因此 T009/T010 标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/events/*`
- 修改：`server/app/main.py`
- 新增：Events domain/repository/API tests
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# Project docs-check passed; ruff passed; mypy passed; 42 passed, 1 warning.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 101 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 并行推进**：完成 `APC-T007` Auth/RBAC 代码与 `APC-T008` dev/in-memory Auth API、seed 脚本。
- **验收状态**：DB-backed repository、seed DB 写入与 audit_log 集成验收仍依赖 PostgreSQL，因此 T007/T008 标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/auth/*`
- 新增：`projects/AI-Parenting-Copilot/server/scripts/seed_family.py`
- 修改：`server/app/main.py`、`server/app/settings.py`
- 新增：Auth service/API 测试
- 修改：项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# Project docs-check passed; ruff passed; mypy passed; 36 passed, 1 warning.
python3 server/scripts/seed_family.py
# dev/in-memory seed JSON output

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 100 轮] 2026-07-09

### 需求变动
- **AI Parenting Copilot 继续推进**：完成 `APC-T004` 核心 schema 代码与 `APC-T006` audit service/decorator 代码。
- **验收状态**：由于当前沙盒无 Docker/PostgreSQL，`APC-T004` 与 `APC-T006` 集成验收无法完成，按 DoD 标记 BLOCKED。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/server/app/models.py`
- 新增：`projects/AI-Parenting-Copilot/server/migrations/versions/0001_initial_schema.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/observability/audit.py`
- 新增：`projects/AI-Parenting-Copilot/server/app/common/audit_decorator.py`
- 新增：schema/audit 相关测试
- 修改：项目级维护文档与 Makefile

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# Project docs-check passed; ruff passed; mypy passed; 30 passed, 1 warning.
python3 -m alembic -c alembic.ini upgrade head --sql
# offline SQL generation passed

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 99 轮] 2026-07-08

### 需求变动
- **AI Parenting Copilot 继续推进**：完成 `APC-T024` Model Gateway 与 `APC-T025` Privacy Adapter。
- **基础设施状态**：`APC-T003` 已完成 Docker Compose / Alembic / DB helper 代码与静态测试，但当前沙盒无 Docker CLI，无法完成容器健康验收，按 DoD 标记 BLOCKED。

### 文件影响
- 新增/修改：`projects/AI-Parenting-Copilot/deploy/*`
- 新增/修改：`projects/AI-Parenting-Copilot/server/app/db.py`、`server/migrations/*`
- 新增：`projects/AI-Parenting-Copilot/server/app/model_gateway/*`
- 新增：`projects/AI-Parenting-Copilot/server/app/privacy/*`
- 新增：`projects/AI-Parenting-Copilot/config/routing_plans.yaml`、`config/models.yaml`
- 新增/修改：项目测试与项目级维护文档

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# Project docs-check passed; ruff passed; mypy passed; 25 passed, 1 warning.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 98 轮] 2026-07-08

### 需求变动
- **AI Parenting Copilot 继续执行开发**：完成项目级 `APC-T002` FastAPI 应用壳与 `APC-T005` 可观测性基础。
- **任务推进策略**：在不超过上下文情况下尽可能多开发；`APC-T003` 因 Docker 验收依赖未在沙盒标记 DONE，转而完成依赖已满足的 `APC-T005`。

### 文件影响
- 新增/修改：`projects/AI-Parenting-Copilot/server/app/*`
- 新增：`projects/AI-Parenting-Copilot/tests/test_settings_ids_errors.py`
- 新增：`projects/AI-Parenting-Copilot/tests/test_app_health_observability.py`
- 修改：`projects/AI-Parenting-Copilot/Makefile`、`pyproject.toml`、`.env.example`
- 修改：项目级 `docs/TASK_BACKLOG.md`、`PROJECT_STATE.md`、`DEV_LOG.md`、`CHANGELOG.md`、`HANDOFF.md`

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# Project docs-check passed; ruff passed; mypy passed; 11 passed, 1 warning.
python3 -m uvicorn server.app.main:app --host 127.0.0.1 --port 8765
# /healthz smoke: HTTP 200

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## [第 97 轮] 2026-07-08

### 需求变动
- **AI Parenting Copilot 项目进入执行阶段**：用户批准开始开发并确认 SSH Deploy Key 已添加。
- **项目文档隔离落地**：在 `projects/AI-Parenting-Copilot/` 内创建项目级 README、维护文档、ADR、Makefile 与基础目录骨架。
- **路径与资料来源澄清**：统一项目目录大小写为 `projects/AI-Parenting-Copilot/`；工厂能力背景直接使用工厂根目录 `PROJECT_DOSSIER_V5.md`。
- **临时文件清理**：删除项目 docs 下 Office 临时锁文件。

### 文件影响
- 新增：`projects/AI-Parenting-Copilot/README.md`、`Makefile`、`pyproject.toml`、`.env.example`、`.gitignore`
- 新增：`projects/AI-Parenting-Copilot/docs/PROJECT_STATE.md`、`DEV_LOG.md`、`CHANGELOG.md`、`HANDOFF.md`、`docs/ADR/ADR-001-project-bootstrap.md`
- 新增：`projects/AI-Parenting-Copilot/server/app/__init__.py`、`tests/test_project_structure.py` 及目录占位文件
- 修改：项目级 `ARCHITECTURE_FINAL.md`、`ENGINEERING_DESIGN.md`、`TASK_BACKLOG.md`（仅路径/资料来源/任务状态同步）
- 删除：`projects/AI-Parenting-Copilot/docs/~$TASK_BACKLOG家庭私有化 AI 育儿副驾驶系统-gpt-5.5-high.docx`

### 验证
```bash
cd projects/AI-Parenting-Copilot
make docs-check && make lint && make typecheck && make test
# Project docs-check passed; ruff passed; mypy passed; 3 passed.

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

## [第 96 轮] 2026-07-07

### 需求变动
- **全功能最小示例确认**：用户确认 `docs/全功能最小示例项目.md` 已测试完成且全部通过。
- **资产卷宗升级**：在保留 `PROJECT_DOSSIER_V4.md` 的前提下，新增 `PROJECT_DOSSIER_V5.md`，同步 FEOS MVP、测试基线、全功能最小示例通过状态和当前资产状态。
- **新项目文档整理建议**：新增根文档与项目文档隔离建议，推荐新项目使用 `projects/<new-project-slug>/docs/`，避免无前缀根目录文档干扰工厂级 SSOT。

### 文件影响
- 新增：`PROJECT_DOSSIER_V5.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

## [第 95 轮] 2026-07-01

### 需求变动
- **FEOS 开发收尾**：对 FEOS 当前实现进行分析、检查、完善，修复基础 Clipboard export workflow 的默认采集范围，确保 MVP smoke 可运行。
- **工厂使用手册重写**：以最新项目状态重写为 FEOS MVP 基础闭环版。
- **全功能最小示例项目重设计**：改为 `mini-feos-debug-lab`，覆盖 FORGE + Network + FEOS 全流程。
- **能力覆盖矩阵更新**：同步 FEOS MVP 能力覆盖。

### 文件影响
- 修改：`_infra/feos/workflows/clipboard_escalation_workflow.py`
- 修改：`docs/工厂使用手册.md`
- 修改：`docs/全功能最小示例项目.md`
- 修改：`docs/工厂能力覆盖检查.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/PROJECT_STATE.md`
- 自动更新：`docs/DOCUMENT_INDEX.md`、`docs/AGENT_HANDOFF_SUMMARY.md`、`docs/GOVERNANCE_CHECK_2026-07-01.md`、`docs/GOVERNANCE_CHECK_LATEST.md`

### 验证
```bash
make feos-test
# 110 passed
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 358 passed, 3 skipped, 44 warnings
make docs-check
# Blockers: 0
```

---

## [第 94 轮] 2026-07-01

### 需求变动
- **FEOS Foundation 批量推进**：根据用户要求，在一次独立开发会话中尽可能多完成 FEOS Task，完成 FEOS-001~FEOS-056 MVP 基础闭环，包括 Foundation、Case Lifecycle、Evidence/Graph、Policy/Context/Package/Clipboard、Response/Verification/Execution/Knowledge、Observability、E2E、Tests、Governance。

### 文件影响
- 新增/修改：`_infra/feos/models/*`
- 新增：`_infra/feos/errors.py`
- 新增：`_infra/feos/storage/*`
- 新增：`_infra/feos/tests/unit/test_ids_enums_errors.py`
- 新增：`_infra/feos/tests/unit/test_case_models.py`
- 新增：`_infra/feos/tests/unit/test_evidence_graph_models.py`
- 新增：`_infra/feos/tests/unit/test_context_package_gateway_models.py`
- 新增：`_infra/feos/tests/unit/test_verification_execution_knowledge_models.py`
- 新增：`_infra/feos/tests/unit/test_workspace_path_guard.py`
- 新增：`_infra/feos/tests/unit/test_storage_primitives.py`
- 新增：`_infra/feos/repositories/*`
- 新增：`_infra/feos/tests/unit/test_case_timeline_repository.py`
- 新增：`_infra/feos/tests/unit/test_artifact_repositories.py`
- 新增：`_infra/feos/case_manager/*`
- 新增：`_infra/feos/cli.py`
- 新增：`_infra/feos/facade.py`
- 新增：`_infra/feos/workflows/*`
- 新增：`_infra/feos/tests/unit/test_case_state_machine.py`
- 新增：`_infra/feos/tests/unit/test_case_service.py`
- 新增：`_infra/feos/tests/unit/test_cli_basic.py`
- 新增：`_infra/feos/tests/unit/test_facade_bootstrap.py`
- 新增：`_infra/feos/tests/unit/test_workflow_guards.py`
- 新增：`_infra/feos/detector/*`
- 新增：`_infra/feos/evidence/*`
- 新增：`_infra/feos/ports/collectors.py`
- 新增：`_infra/feos/adapters/git_adapter.py`
- 新增：`_infra/feos/graph/*`
- 新增：相关 detector/evidence/collector/graph 单元测试
- 新增：`_infra/feos/retrieval/*`
- 新增：`_infra/feos/hypothesis/*`
- 新增：`_infra/feos/policy/*`
- 新增：`_infra/feos/adapters/privacy_adapter.py`
- 新增：`_infra/feos/adapters/local_rag_adapter.py`
- 新增：相关 retrieval/hypothesis/privacy/policy 单元和安全测试
- 新增：`_infra/feos/context/*`
- 新增：`_infra/feos/package/*`
- 新增：`_infra/feos/renderers/*`
- 新增：`_infra/feos/gateways/*`
- 新增：`_infra/feos/ports/renderers.py`
- 新增：`_infra/feos/ports/gateways.py`
- 新增：相关 context/package/renderer/gateway/clipboard export 单元与 golden tests
- 新增：`_infra/feos/ingestion/*`
- 新增：`_infra/feos/verification/*`
- 新增：`_infra/feos/execution/*`
- 新增：`_infra/feos/distillation/*`
- 新增：`_infra/feos/adapters/clipboard_adapter.py`
- 新增：`_infra/feos/adapters/knowledge_os_adapter.py`
- 新增：相关 response/verification/execution/knowledge 单元测试
- 新增：`_infra/feos/observability/*`
- 新增：`scripts/diagnostics/feos_case_audit.py`
- 新增：`_infra/feos/workflows/clipboard_escalation_workflow.py`
- 新增：`_infra/feos/workflows/response_processing_workflow.py`
- 新增：`_infra/feos/workflows/execution_closure_workflow.py`
- 新增：`_infra/feos/tests/integration/*`
- 新增：`_infra/feos/tests/unit/test_feos_diagnostics.py`
- 修改：`Makefile`
- 修改：`FEOS_TASK_BACKLOG.md`
- 补丁：`ClipboardEscalationWorkflow.collect()` 默认只启用 `user_input` collector，避免基础 export smoke 自动采集 canary/security config 导致 policy block。
- 修改：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 验证
```bash
python3 -m pytest _infra/feos/tests/unit -q
# 110 passed
python3 -m compileall -q _infra/feos
# pass
```

---

## [第 93 轮] 2026-07-01

### 需求变动
- **FEOS-002 实现**：实现 FEOS 配置加载器与 Bootstrap 基础，支持 defaults、项目配置、`.env`、环境变量和 CLI overrides。

### 文件影响
- 新增：`_infra/feos/config_loader.py`
- 新增：`_infra/feos/bootstrap.py`
- 新增：`_infra/feos/tests/unit/test_config_loader.py`
- 修改：`_infra/feos/__init__.py`
- 修改：`_infra/feos/tests/unit/test_package_import.py`
- 修改：`FEOS_TASK_BACKLOG.md`
- 修改：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 验证
```bash
python3 -m pytest _infra/feos/tests/unit/test_package_import.py _infra/feos/tests/unit/test_config_loader.py -q
# 12 passed
python3 -m compileall -q _infra/feos
# pass
```

---

## [第 92 轮] 2026-07-01

### 需求变动
- **FEOS-001 实现**：按 FEOS 架构/工程设计/Backlog 创建 FEOS 模块骨架、默认配置、默认 policy/profile 文件和 runtime gitignore 规则。

### 文件影响
- 新增：`_infra/feos/__init__.py`
- 新增：`_infra/feos/defaults/feos.yaml`
- 新增：`_infra/feos/defaults/policies/default.yaml`
- 新增：`_infra/feos/defaults/policies/redaction.yaml`
- 新增：`_infra/feos/defaults/policies/gateway.yaml`
- 新增：`_infra/feos/defaults/renderer_profiles/gpt_markdown_debug.yaml`
- 新增：`_infra/feos/defaults/renderer_profiles/claude_markdown_architecture.yaml`
- 新增：`_infra/feos/defaults/renderer_profiles/generic_markdown.yaml`
- 新增：`_infra/feos/defaults/renderer_profiles/api_json.yaml`
- 新增：`_infra/feos/defaults/renderer_profiles/mcp_message.yaml`
- 新增：`config/feos.yaml`
- 新增：`_infra/feos/tests/unit/test_package_import.py`
- 修改：`.gitignore`
- 修改：`FEOS_TASK_BACKLOG.md`
- 修改：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 验证
```bash
python3 -m pytest _infra/feos/tests/unit/test_package_import.py -q
# 5 passed
python3 -m compileall -q _infra/feos
# pass
```

---

## [第 78 轮] 2026-06-25

### 需求变动
- **联网功能开发5：搜索风控系统性加固**：按用户最新 P0 指令“附录 1”处理搜索引擎连续 CAPTCHA / 429 / challenge 问题。
- **架构约束说明**：保留 SearXNG 作为 Primary Search，不替换 Crawl4AI Primary Extract；新增 API fallback 仅在 API key 环境变量存在时自动启用，密钥不进入仓库。
- **新增能力**：Engine Matrix 白名单配置、per-engine Circuit Breaker、MultiSourceSearchOrchestrator、Brave/Tavily/Serper optional fallback、curl_cffi optional TLS fallback、诊断工具 v2。

### 文件影响
- 新增：`_infra/network/search/circuit_breaker.py`
- 新增：`_infra/network/search/api_providers.py`
- 新增：`_infra/network/search/orchestrator.py`
- 新增：`_infra/network/extract/curl_cffi_fallback.py`
- 新增：`_infra/network/tests/unit/test_circuit_breaker.py`
- 新增：`_infra/network/tests/unit/test_search_orchestrator.py`
- 新增：`_infra/network/tests/unit/test_curl_cffi_fallback.py`
- 修改：`_infra/network/search/searxng_client.py`
- 修改：`_infra/network/network_workflow/workflow.py`
- 修改：`_infra/network/extract/extractor_chain.py`
- 修改：`docker/searxng/settings.yml`
- 修改：`config/network.yaml`
- 修改：`scripts/diagnostics/test_engine_risk_control.py`
- 修改：`requirements.txt`
- 修改测试：`test_search.py`、`test_workflow.py`、`test_docker_services.py`
- 文档：`TASK_BACKLOG.md`、`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/SEARCH_ENGINE_RISK_CONTROL_REPORT.md`

### 验证
```bash
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 358 passed, 3 skipped, 44 warnings
python3 -m compileall -q _infra/network scripts/diagnostics
# pass
python3 -m _infra.network.cli config
# Network Config loaded successfully
```

---

### 第 78 轮补丁（2026-06-25）

#### 需求变动
- **真机日志兼容修正**：根据用户 SearXNG 2026.6.22 运行日志，移除 google/brave/startpage partial engine override，避免 SearXNG 报 “engine field is missing”。
- **健康检查降噪**：Docker healthcheck 改为只查询 `engines=wikipedia`，避免每次健康检查触发 Mojeek/Qwant 403 suspended 日志。

#### 文件影响
- 修改：`docker/searxng/settings.yml`
- 修改：`docker/docker-compose.yml`
- 修改：`_infra/network/tests/unit/test_docker_services.py`
- 文档：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`

---

### 第 78 轮补丁 2（2026-06-25）

#### 需求变动
- **按真机诊断结果收敛默认引擎池**：根据用户诊断输出，默认路由避开 bing/qwant/mojeek/reddit/yahoo/duckduckgo 等当前代理出口高风险或低成功率引擎。
- **保留 API fallback**：Tavily / Serper 已在用户本地 export 并被 Orchestrator 成功加载，默认 web coverage 不足时交给 API fallback。
- **保留 Wikipedia 特殊角色**：Wikipedia 虽在泛 query 诊断中被判 BROKEN，但 ping 与知识查询可用，因此保留为知识/healthcheck 引擎，不再作为 broad web search 主池。

#### 文件影响
- 修改：`_infra/network/search/searxng_client.py`
- 修改：`_infra/network/search/orchestrator.py`
- 修改：`config/network.yaml`
- 修改：`docker/searxng/settings.yml`
- 文档：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`

---

## [第 79 轮] 2026-06-25

### 需求变动
- **本地 API Key 持久化**：新增 `.env.example` 与本地 `.env` 自动加载能力，用户不再需要每次打开终端手动 `export TAVILY_API_KEY` / `SERPER_API_KEY`。
- **联网功能最终收尾**：对照架构/工程设计，收敛密钥管理与提取 fallback 超时问题；保持既有 Search → Extract → Privacy → RAG 架构边界不变。
- **提取体验优化**：`TrafilaturaProvider` 增加 8s bounded timeout，避免无法直连 GitHub/HackerNews 时长时间阻塞。

### 文件影响
- 新增：`.env.example`
- 新增：`_infra/network/tests/unit/test_env_loader.py`
- 新增：`_infra/network/tests/unit/test_trafilatura_timeout.py`
- 修改：`_infra/network/core/secrets.py`
- 修改：`_infra/network/config_loader/loader.py`
- 修改：`_infra/network/search/orchestrator.py`
- 修改：`_infra/network/extract/trafilatura_fallback.py`
- 修改：`_infra/.env.example`
- 文档：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`_infra/network/README.md`

### 验证
```bash
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 358 passed, 3 skipped, 44 warnings
python3 -m compileall -q _infra/network scripts/diagnostics
# pass
python3 -m _infra.network.cli config
# Network Config loaded successfully
```

---

## [第 80 轮] 2026-06-25

### 需求变动
- **全功能示例项目与培训文档重写**：用户要求在联网功能确认打通后，面向零基础用户更新完整工厂使用手册、重新生成全功能最小示例项目，并建立能力覆盖矩阵。
- **提取 fallback 收尾修正**：根据用户端到端日志，避免 trafilatura 超时后后台线程继续输出底层下载错误，改为 bounded async HTTP fetch + trafilatura extraction。

### 文件影响
- 重写：`docs/工厂使用手册.md`
- 重写：`docs/全功能最小示例项目.md`
- 重写：`docs/工厂能力覆盖检查.md`
- 修改：`README.md`
- 修改：`HANDOFF.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`_infra/network/extract/trafilatura_fallback.py`
- 修改：`_infra/network/tests/unit/test_trafilatura_timeout.py`

### 验证
```bash
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 358 passed, 3 skipped, 44 warnings
python3 -m compileall -q _infra/network scripts/diagnostics
# pass
python3 -m _infra.network.cli config
# Network Config loaded successfully
```

---

## [第 81 轮] 2026-06-25

### 需求变动
- **Claude Code for VS Code 主工作流补充**：培训文档必须反映用户日常通过 VS Code Claude Code 自然语言对话使用工厂，而不是仅通过终端 CLI。
- **全功能最小示例升级**：示例项目必须包含所有功能，包括高风险功能；高风险能力采用 sandbox / dry-run / approval / deny-test 方式安全覆盖。
- **文档治理自动化常态化方案**：基于 `DOCUMENT_AUDIT_REPORT.md` 与相关治理文档，形成可执行自动化方案并升级治理脚本。

### 文件影响
- 修改：`docs/工厂使用手册.md`
- 修改：`docs/全功能最小示例项目.md`
- 修改：`docs/工厂能力覆盖检查.md`
- 新增：`docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`
- 新增：`docs/adr/ADR-008-documentation-governance-automation.md`
- 修改：`docs/adr/README.md`
- 修改：`scripts/governance_check.py`
- 修改：`Makefile`
- 修改：`README.md`
- 修改：`HANDOFF.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
python3 scripts/governance_check.py --strict
# Blockers: 0; Warnings: 0
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 358 passed, 3 skipped, 44 warnings
python3 -m compileall -q _infra/network scripts/diagnostics
# pass
```

---

## [第 82 轮] 2026-06-25

### 需求变动
- **文档治理 P1 自动化落地**：实现 changed-files R5 检查、Backlog/DEV_LOG 同步检查、代码变更必须更新 CHANGELOG、架构触发词提示 ADR、自动生成 `docs/DOCUMENT_INDEX.md`。

### 文件影响
- 修改：`scripts/governance_check.py`（P1 自动化；后续补丁排除 `.pytest_cache` 等测试缓存）
- 新增/自动生成：`docs/DOCUMENT_INDEX.md`
- 修改：`docs/GOVERNANCE_CHECK_2026-06-25.md`
- 修改：`docs/GOVERNANCE_CHECK_LATEST.md`
- 修改：`docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`TASK_BACKLOG.md`

### 验证
```bash
python3 scripts/governance_check.py --strict
# Blockers: 0
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 358 passed, 3 skipped, 44 warnings
python3 -m compileall -q _infra/network scripts/diagnostics
# pass
```

---

## [第 83 轮] 2026-06-25

### 需求变动
- **文档治理 P2 自动化落地**：实现本地 pre-commit 集成、GitHub Actions 治理检查、每周 launchd 治理检查、自动生成新 Agent 接手摘要，并将提交前 docs-check 改为 no-write strict 模式。

### 文件影响
- 新增：`scripts/hooks/pre_commit_governance.sh`
- 新增：`scripts/install_governance_hooks.sh`
- 新增：`scripts/launchd/com.forge.governance-check.plist`
- 新增：`.github/workflows/governance.yml`
- 新增/自动生成：`docs/AGENT_HANDOFF_SUMMARY.md`
- 修改：`scripts/governance_check.py`
- 修改：`Makefile`
- 修改：`docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`
- 修改：`docs/DOCUMENT_INDEX.md`
- 修改：`docs/GOVERNANCE_CHECK_2026-06-25.md`
- 修改：`docs/GOVERNANCE_CHECK_LATEST.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`TASK_BACKLOG.md`

### 验证
```bash
make docs-check
python3 scripts/governance_check.py --strict
python3 -m compileall -q scripts/governance_check.py
```

---

## [第 84 轮] 2026-06-25

### 需求变动
- **Claude Code for VS Code 本地模型 alias 兼容修复**：用户当前 VS Code Claude Code 只连接本地开源模型，但插件报选中模型不存在或无权限；补充当前 UI 中 Opus 4.8 / Sonnet 4.6 / Haiku 4.5 对应 alias 到本地 MTPLX 主模型映射。
- **4000 端口旧进程占用修复**：用户 curl `/v1/messages` 返回 Not Found，原因是 4000 被旧代理进程占用；`scripts/forge-start.sh` 改为按端口清理 4000/4001。

### 文件影响
- 修改：`_infra/litellm-config.yaml`
- 修改：`_infra/smart_proxy.py`
- 修改：`_infra/litellm_gatekeeper.py`
- 修改：`scripts/forge-start.sh`
- 修改：`docs/工厂使用手册.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/PROJECT_STATE.md`

### 补丁：Claude Code Streaming 响应与 max_tokens 收敛
- 修复 VS Code Claude Code `stream=true` 时本地代理按非流式读取导致 UI 长时间等待的问题。
- `_infra/smart_proxy.py` 增加 Anthropic SSE 事件转换，并默认限制本地输出 `FORGE_CLAUDE_CODE_MAX_TOKENS=1024`。

### 补丁 2：修复 Claude Code 空流式响应
- 用户验证 `curl -N /v1/messages` 只有 start/stop 没有文本 delta。
- 根因：MTPLX 对 `stream=true` 返回完整 OpenAI JSON，不返回 SSE `data:` 行。
- 修复：Claude Code streaming 路径对后端改用非流式 JSON，再包装成 Anthropic SSE `content_block_delta`。

### 补丁 3：Claude Code for VS Code 操作说明修正
- 明确 `Developer: Reload Window` 是 VS Code 命令面板命令，不是终端命令。
- 明确 `code .` 需要安装 Shell Command，不是必需步骤。
- 手册与示例项目改为优先使用 `@文件` 附加上下文，避免本地模型一次性自行读取多个长文档导致卡顿。

### 验证
```bash
python3 -m compileall -q _infra/smart_proxy.py _infra/litellm_gatekeeper.py
python3 -c "import yaml; from pathlib import Path; cfg=yaml.safe_load(Path('_infra/litellm-config.yaml').read_text()); assert any(m['model_name'] == 'claude-opus-4-1' for m in cfg['model_list'])"
```

---

## [第 85 轮] 2026-06-26

### 需求变动
- **Claude Code 本地模型操作体验与自助排障完善**：补充 VS Code 命令面板与终端命令区别、等待时间预期、max token 建议、流式输出状态、卡死判断、模型卸载/重载方式。
- **全功能示例项目自包含启动命令**：示例文档新增本地模型网关、SearXNG、curl streaming、联网搜索验证和故障恢复命令，减少对使用手册的依赖。

### 文件影响
- 新增：`scripts/model_status.sh`
- 新增：`scripts/stop_local_models.sh`
- 修改：`_infra/smart_proxy.py`
- 修改：`docs/工厂使用手册.md`
- 修改：`docs/全功能最小示例项目.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`TASK_BACKLOG.md`

### 验证
```bash
python3 -m compileall -q _infra/smart_proxy.py
make docs-check
```

---

## [第 86 轮] 2026-06-26

### 需求变动
- **记录 Claude Code 长文档恢复经验**：用户确认 `@HANDOFF.md` 同样提示词已从 20 分钟无输出改善为约 2 分钟输出，需记录经验并分析原因。
- **新增本地流式诊断工具**：用于验证 MTPLX 后端是否真 OpenAI SSE 流式，以及 Smart Proxy 是否输出 Anthropic `content_block_delta`。

### 文件影响
- 新增：`scripts/diagnostics/test_local_streaming.py`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/工厂使用手册.md`

### 验证
```bash
python3 -m compileall -q scripts/diagnostics/test_local_streaming.py
```

---

## [第 87 轮] 2026-06-26

### 需求变动
- **本地模型运行参数 SSOT**：用户要求 MTPLX / Ollama / llama.cpp 等本地模型启动参数可自定义，不再散落硬编码。
- **推理加速与 MTP 验证**：纳入 Ollama `OLLAMA_FLASH_ATTENTION=1`、`OLLAMA_KV_CACHE_TYPE=q4_0`，并新增 MTP / speculative decoding 生效诊断。
- **真流式诊断说明**：补充如何判断后端是真 OpenAI SSE streaming、单 delta、完整 JSON fallback，还是仅 Smart Proxy 包装。

### 文件影响
- 新增：`docs/adr/ADR-009-local-model-runtime-configuration.md`
- 修改：`docs/adr/README.md`
- 新增：`config/model_runtime.yaml`
- 新增：`_infra/model_runtime.py`
- 新增：`scripts/diagnostics/test_mtp_effectiveness.py`
- 新增：`docs/LOCAL_MODEL_RUNTIME_TUNING.md`
- 修改：`scripts/forge-start.sh`
- 修改：`_factory/patterns/peer-review/src/peer_review/llm_client.py`
- 修改：`_infra/smart_proxy.py`
- 修改：`config/models.yaml`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`TASK_BACKLOG.md`

### 补丁：显式写入 MTPLX 加速参数与日志说明
- 8080 Qwen：`--profile sustained --mtp --depth 3 --stream-interval 1 --reasoning off --max-tokens 2048`。
- 8082 Gemma：`--profile sustained --mtp --depth 6 --stream-interval 1 --reasoning off --max-tokens 2048`。
- `docs/LOCAL_MODEL_RUNTIME_TUNING.md` 增加 `/tmp/mtplx_8080.log`、`/private/tmp/mtplx_8080.log` 等日志位置说明。

### 补丁 2：真机 MTP 证据与 A/B 注意事项
- 记录用户真机日志：Qwen/Gemma 均显示 Sustained MTP；Gemma assistant MTP drafter active；Qwopus llama.cpp 显示 MTP context。
- `test_mtp_effectiveness.py` 增加 `mtplx_openai_generation` JSON metrics 解析，便于比较 `elapsed_s`、`tok_s`、`end_to_end_tok_s`。
- 明确 `--no-mtp` 对照必须清日志、重启、固定 prompt/max_tokens/temperature/top_p/seed，否则不能严谨比较。

### 验证
```bash
python3 _infra/model_runtime.py command 8084
python3 _infra/model_runtime.py env-shell ollama
python3 scripts/diagnostics/test_mtp_effectiveness.py
python3 -m compileall -q _infra/model_runtime.py scripts/diagnostics/test_mtp_effectiveness.py
```

---

## [第 88 轮] 2026-06-26

### 需求变动
- **记录 MTP A/B 真机结果**：用户提供短 prompt 下 MTP on / no-MTP 对比结果，以及 `test_local_streaming.py` direct backend refused / proxy ok 的解释需求。
- **操作指令输出风格要求**：用户要求今后操作指令集中放在回复最后，不要穿插在解释过程中。

### 文件影响
- 修改：`HANDOFF.md`
- 修改：`docs/LOCAL_MODEL_RUNTIME_TUNING.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`

### 验证
```bash
make docs-check
```

---

## [第 89 轮] 2026-06-26

### 需求变动
- **一键本地运行时综合 Benchmark**：用户反馈手工 MTP/no-MTP/KV cache/streaming 测试繁琐且容易出错，要求提供一键全面测试并生成可发送的测试产物。

### 文件影响
- 新增：`scripts/diagnostics/benchmark_local_runtime.py`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`docs/LOCAL_MODEL_RUNTIME_TUNING.md`
- 修改：`TASK_BACKLOG.md`

### 补丁：Benchmark 超时修复与 proxy-only 启动模式
- 修复 `TimeoutExpired.stdout` bytes/str 拼接导致的 TypeError。
- 新增 `--startup-mode proxy-only` 默认模式，只启动 4001/4000，由 Smart Proxy 按需加载 8080，避免每个 profile 完整自检 8080/8082/8084。

### 补丁 2：最终版 Benchmark
- 默认补齐 `controlled_medium` 与 `controlled_long_context`，覆盖长上下文 + 中长输出。
- 默认 profile 覆盖 `mtp_depth3`、`no_mtp`、`mtp_depth3_kv_q8`、`mtp_depth3_kv_q4`。
- 新增 `--repeat`、`--seed`、aggregate mean/std 汇总。
- 默认跳过主流程 stream 请求，每个 profile 仍保留独立 streaming diagnostics。

### 验证
```bash
python3 -m compileall -q scripts/diagnostics/benchmark_local_runtime.py
```

---

## [第 90 轮] 2026-07-01

### 需求变动
- **Project Dossier V4**：用户要求在 MTP 测试收尾后，全面更新维护文档，并新增 `PROJECT_DOSSIER_V4.md`，作为当前项目资产卷宗。
- **范围修正**：V4 只记录当前资产、边界、运行方式和可扩展点，不写入任何未获批准的新业务系统设计。

### 文件影响
- 新增：`PROJECT_DOSSIER_V4.md`
- 修改：`HANDOFF.md`
- 修改：`README.md`
- 修改：`docs/PROJECT_STATE.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`TASK_BACKLOG.md`
- 自动更新：`docs/DOCUMENT_INDEX.md`、`docs/AGENT_HANDOFF_SUMMARY.md`、`docs/GOVERNANCE_CHECK_2026-06-26.md`、`docs/GOVERNANCE_CHECK_LATEST.md`

### 验证
```bash
make docs-check
python3 -m compileall -q scripts/governance_check.py
```

---

## [第 91 轮] 2026-07-01

### 需求变动
- **R5 Header 治理规则修正**：用户明确手写文档不应因缺少 LLM header 被阻断；LLM header 仅针对 LLM 生成/修改文件。

### 文件影响
- 修改：`scripts/governance_check.py`
- 修改：`HANDOFF.md`
- 修改：`docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`
- 修改：`docs/DEV_LOG.md`
- 修改：`docs/CHANGELOG.md`
- 修改：`TASK_BACKLOG.md`

### 验证
```bash
make docs-check
```

---

## [第 60 轮] 2026-06-24

### 需求变动
- **生成问题诊断包 (PDP)**：遵照老板指令不修改代码，针对各大搜索引擎反爬风控拦截问题，输出完整档案 `docs/PROBLEM_DIAGNOSTIC_PACKAGE.md`。

### 文件影响
- 新增：`docs/PROBLEM_DIAGNOSTIC_PACKAGE.md`
- 文档：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`


## [第 50 轮] 2026-06-24

### 需求变动
- **生成完整问题包 (PDP)**：遵照老板指令不修改代码，针对各大搜索引擎验证码及 429 反爬风控拦截问题，输出完整信息包 `docs/PROBLEM_DIAGNOSTIC_PACKAGE.md`。

### 文件影响
- 新增：`docs/PROBLEM_DIAGNOSTIC_PACKAGE.md`
- 文档：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`

## [第 44 轮] 2026-06-20

### 需求变动
- **重大治理行动**：生成 Project Dossier V2 – 项目资产审计 + 架构逆向工程 + 知识压缩，面向下一任架构师接管与升级设计。
- **新增**：`docs/dossier_v2/` 目录及 6 个交付物：
  - `PROJECT_DOSSIER_V2.md` – 卷宗正文（17 章，含 Executive Takeover Brief / As-Is Architecture / Risk Register / 30/60/90 Day Handover Plan）
  - `asset_manifest.json` – 18 项资产清单（P0/P1/P2）
  - `evidence_index.csv` – 50 条证据索引（Observed/Inferred/Intended/Recommended）
  - `risk_register.csv` – 20 项风险/技术债登记
  - `adr_candidates.md` – 7 个 ADR 候选（网关熔断/测试替身/配置统一/容器化/可观测/密钥Vault/ModelLauncher抽象）
  - `diagram_sources.md` – 8 张架构图源与证据映射
- **识别 Top 风险**：R-001 Proxy 单点无熔断 / R-002 VRAM LRU竞态 / R-003 无CI/CD / R-009 测试覆盖<15%
- **识别承重墙**：smart_proxy_streaming.py / llm_client.py / config 三文件 SSOT / ReviewState
- **输出接管计划**：30/60/90 Day – 测试护栏→网关加固→配置收敛→CI→可观测→容器化→多租户
- **版本提升**：v1.2.9 → v1.3.0-dossier

### 文件影响
- 新增：`docs/dossier_v2/PROJECT_DOSSIER_V2.md`、`docs/dossier_v2/asset_manifest.json`、`docs/dossier_v2/evidence_index.csv`、`docs/dossier_v2/risk_register.csv`、`docs/dossier_v2/adr_candidates.md`、`docs/dossier_v2/diagram_sources.md`
- 改动：`docs/PROJECT_STATE.md`（版本 v1.3.0-dossier，新增 Dossier 交付物索引与接管必读顺序，待办更新为 P0 三项）
- 改动：`HANDOFF.md`（版本 v1.3.0，第 44 轮修订，接手必读顺序首位增加 Dossier）
- 改动：`docs/CHANGELOG.md`（本文件）

### 说明
- 本轮为纯文档治理轮，无代码改动。所有结论基于代码/配置证据，严格区分 Observed/Inferred/Intended/Recommended。
- Dossier 明确标注：Proxy单点、VRAM竞态、无CI、测试覆盖低为真危险；ReviewState/三文件SSOT/字段白名单为不可轻动项。
- 下一轮建议优先落地 ADR-C002 测试替身 → ADR-C003 配置统一 → ADR-C001 网关加固。

---


## [第 43 轮] 2026-06-20

### 需求变动
- **重大治理行动**：执行 Repository Cleanup & Obsolete Asset Management，并按用户最新要求修正 `_obsolete/` 策略。
- **明确保留 active**：`projects/legal-bot/`、`projects/project-b/`、`retro-data-share/` 不迁移，继续保留在 GitHub 仓库。
- **明确追溯策略**：`_obsolete/` 不 ignore，继续 push 到 GitHub，作为历史资产追溯目录。
- **新增**：`docs/repository-audit.md`、`docs/repository-cleanup-report.md`、`_obsolete/README.md`。
- **迁移到 `_obsolete/`**：一次性诊断/修复脚本、运行日志、历史设计文档、旧 Agno/orchestrator 实现、历史诊断输出。
- **修复**：恢复 `peer_review.orchestrator` 极薄 lazy 兼容 shim，解决源码/测试引用与旧实现迁移之间的不一致。
- **优化**：扩展 `.gitignore`，覆盖 build、cache、logs、runtime、temp、Python、Node、IDE、OS 产物，同时不忽略 `_obsolete/`。

### 文件影响
- 新增/更新：`docs/repository-audit.md`、`docs/repository-cleanup-report.md`、`_obsolete/README.md`、`_factory/patterns/peer-review/src/peer_review/orchestrator.py`（兼容 shim）。
- 改动：`.gitignore`、`README.md`、`HANDOFF.md`、`docs/ARCHITECTURE.md`、`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`。
- 迁移：详见 `_obsolete/README.md` 与 `docs/repository-cleanup-report.md`。

### 说明
- 本轮最终状态：指定三个目录保持 active；`_obsolete/` 保持 tracked 并 push 到 GitHub。
- 源码与旧文档冲突处，以当前源码为准，并记录在 `docs/repository-audit.md`。

---


## [第 1 轮] 2026-06-10

### 需求变动
- **新增**：建立 FORGE Factory 基础设施骨架（Phase 1）。
- **新增**：接力维护文档体系（应对意外中止可接续）—— 来自特殊要求 #1。
- **新增**：每轮需求增删改要同步到相关文档并写变动说明 —— 来自特殊要求 #2（本 CHANGELOG 即其落地）。
- **新增**：每轮改动后打 zip 补丁包 —— 来自补丁约定。（**已于 2026-06-16 Documentation Governance 审计中正式废弃**，见 DOCUMENT_AUDIT_REPORT.md + HANDOFF.md 同步方式更新）

### 文件影响（新增）
- `HANDOFF.md`（接力总入口）
- `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`、`docs/CHANGELOG.md`、`docs/REAL_MACHINE_VALIDATION.md`
- `_infra/`、`_factory/`、`_agents/`、`projects/` 目录骨架及其内容（本轮陆续生成，见 PROJECT_STATE.md 勾选表）

### 文件影响（本轮最终清单）
**新增（_infra）**：litellm-config.yaml、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md、forge_tools/（pyproject + src/forge/{__init__,task_graph,phases,cli}.py + tests/{test_task_graph,test_phases,test_cli}.py）
**新增（_factory）**：skills/{_TEMPLATE,discovery-interview,arch-design,tdd-cycle,security-review}.skill.md、patterns/fastapi-backend/（README+pyproject+src/app/{__init__,core,config,main}.py+tests/{unit,integration}）、lessons/_TEMPLATE.lesson.md
**新增（_agents）**：arch-advisor、security-reviewer、code-explorer、retro-analyst
**新增（projects/_TEMPLATE）**：AGENTS.md、.claude/{CLAUDE.md,hooks/*,agents/*,*-runner.sh}、docs/{DISCOVERY,SPEC,RISK,BUILD_LOG,TASK_GRAPH}.md、docs/{adr,specs,harden,external-review}/*
**新增（根/docs）**：README.md、docs/REAL_MACHINE_VALIDATION.md
**改动**：`.gitignore` 由上个项目（soundproof-agent）残留规则改写为契合 forge 体系。

### 说明
- 这是项目第一轮，绝大多数为"从无到有"的新增，无删除/改动既有需求。
- GLM 型号/Key 为"待补全"状态（占位 glm-5.1），属约定中的占位，非遗漏。

---

## [第 2 轮] 2026-06-10

### 需求变动
- **改动**：GLM 云端接入由"智谱官网占位"改为"经 ModelScope（魔搭）接入 GLM-5"。
- **修复**：setup.sh 在 macOS 老 bash 下的 `unbound variable` 报错。
- **澄清**：Claude Code 接入方式（环境变量，非 settings.json）。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（cloud/glm-primary → ModelScope，model 加 openai/ 前缀）
- **改动**：`_infra/.env.example`（GLM_API_KEY 说明改为 ModelScope SDK Token）
- **改动**：`_infra/setup.sh`（修参数展开 bug、去 set -u、修 Ollama 版本判断）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 改 ModelScope 双重验证；V-ClaudeCode 补充环境变量说明）
- **改动**：`docs/DECISIONS.md`（D-003 更新为 ModelScope 方案）

### 说明
- 本轮无新增功能需求，均为对第 1 轮产物的"改动/修复/澄清"，对应特殊要求 #2。

---

## [第 3 轮] 2026-06-11

### 需求变动
- **修复**：自检脚本模型名显示乱码。
- **改进**：自检脚本对 litellm 在 venv 中的探测与提示。
- **澄清**：`ollama serve` 端口占用含义、litellm 需先激活 venv。

### 文件影响
- **改动**：`_infra/setup.sh`（模型名查找去 cut；litellm 多路径探测）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-Ollama / V-LiteLLM 补充真机情况说明）

### 说明
- 本轮均为对真机验证中暴露问题的修复/澄清，无新增/删除功能需求（对应特殊要求 #2）。

---

## [第 4 轮] 2026-06-11

### 需求变动
- **修复（诊断中）**：ModelScope 经 LiteLLM 网关卡住 → 加 stream_timeout/drop_params + 诊断模型。
- **新增**：GLM 链路诊断脚本 `_infra/diag-glm.sh`（配合 GitHub 拉取产物的新流程）。
- **新规则**：补丁包只含改动文件（不全量）。
- **新规则**：老板 push 测试产物到 GitHub，Agent 拉取分析。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（cloud/glm-primary 加 stream_timeout+drop_params；新增 cloud/glm-debug）
- **新增**：`_infra/diag-glm.sh`
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 诊断 + V-GLM-DEBUG + 状态汇总）
- **改动**：`HANDOFF.md`（两条新流程规则）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/DECISIONS.md`

### 说明
- 本轮聚焦 GLM 链路诊断与流程优化，对应特殊要求 #2。

---

## [第 5 轮] 2026-06-11

### 需求变动
- **修复**：GLM 经网关失败根因 = 启动进程缺 export GLM_API_KEY（非 ModelScope 问题）。
- **新增**：LiteLLM 启动脚本 `_infra/start-litellm.sh`（自动 export .env）。
- **明确**：GLM 流式可用、非流式不稳（Claude Code 默认流式，不影响日常）。

### 文件影响
- **新增**：`_infra/start-litellm.sh`
- **改动**：`_infra/litellm-config.yaml`（glm-primary 诊断结论注释、timeout/stream_timeout 调整）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 改启动脚本+流式；状态汇总）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/DECISIONS.md`

### 说明
- 首次走通"老板 push 产物 → Agent git pull 分析"流程（D-005）。

---

## [第 6 轮] 2026-06-11

### 需求变动
- **澄清**：GLM 自报"通义千问"是模型身份认知偏差，非 fallback、非调用错误。
- **新增**：GLM 终极验证脚本 `_infra/verify-glm.sh`（基于 x-litellm-model-id）。
- **里程碑**：Phase 1 基础设施核心链路全部打通。

### 文件影响
- **新增**：`_infra/verify-glm.sh`
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 标记✅ + 身份偏差澄清 + x-litellm-model-id 方法）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 说明
- 本轮以澄清+验证工具为主，无功能性需求增删。

---

## [第 7 轮] 2026-06-11

### 需求变动
- **修复**：verify-glm.sh 误报"被 fallback"（v1 只测非流式的设计缺陷）。
- **改进**：diag-glm.sh 增加"直连 ModelScope 非流式"对照项，精准分离根因。

### 文件影响
- **改动**：`_infra/diag-glm.sh`（v2 重写，新增 A1 对照 + 判读指引）
- **改动**：`_infra/verify-glm.sh`（v2 重写，流式/非流式分别判定）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/REAL_MACHINE_VALIDATION.md`

### 说明
- 非流式不稳的根治方案待 diag v2 输出确认后实施；本轮聚焦"把诊断做准"。

---

## [第 8 轮] 2026-06-11

### 需求变动
- **明确定位**：工厂本身=产品，试点项目=陪练（非正式开发目标）。角色=教练&陪练。
- **闭环**：GLM 非流式问题根因=Key 填错，已解决，全链路正常。
- **新增**：3 个本地模型接入（编程专用 + 2 个向量嵌入）。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（新增 local/coder、local/embedding、local/embedding-large；GLM 注释更新）
- **改动**：`_infra/model-routing-rules.md`（新增模型清单表 + 用法）
- **改动**：`HANDOFF.md`（新增 0.0 项目定位）、`docs/DECISIONS.md`（D-007、D-008）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM✅、新增 V-LocalModels）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 说明
- 第7-8两轮合并记录（GLM诊断收尾 + 模型扩充 + 定位澄清）。

---

## [第 9 轮] 2026-06-11

### 需求变动
- **新增**：试点项目 debt-collection（个人合法讨债助手），用于压测工厂 DISCOVERY 阶段。
- **明确边界**：仅合法路径；查财产=指引合法渠道/律师调查令，不自行非法查询；不做施压催收。
- **新增**：工厂能力评估文档 FACTORY_ASSESSMENT.md（陪练核心产出）。

### 文件影响
- **新增**：projects/debt-collection/（复制 _TEMPLATE）+ docs/DISCOVERY.md（填充）+ AGENTS.md（更新项目身份/红线）
- **新增**：docs/FACTORY_ASSESSMENT.md（工厂能力评估 + 改进 backlog FB-1~FB-4）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

### 说明
- 进入 Phase 2 试点。重心是压测工厂、记录能力边界与缺陷，非交付讨债系统本身。

---

## [第 10 轮] 2026-06-11

### 需求变动（老板补充 6 点）
- **新增(工厂级)**：数据收集/整理/提炼/复用能力 + 多源权重 + 数据质量把控（FB-5）。
- **新增(工厂级)**：本地模型联网取数抽象层；授权账号登录须保账号安全（FB-6）。
- **新增(工厂级)**：DISCOVERY 深度讨论自检（FB-7）。
- **新增(工厂级)**：通用 Ingestion 能力层（图片/PDF/录音→结构化），已选型（FB-8）。
- **改动(讨债项目)**：核心标准=实际讨回率；新增 AC-6（执行可行性+回款概率优先，反老赖执行难）。
- **流程**：按老板要求 DISCOVERY 延长，暂不进 SPEC。

### 文件影响
- **新增**：docs/research/ingestion-tools-comparison.md（资料整理工具横向对比）
- **改动**：projects/debt-collection/docs/DISCOVERY.md（第8/9节 + AC-6）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-5~FB-8 + 要点映射）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 11 轮] 2026-06-11

### 需求变动（老板决策）
- **FB-6 取数**：定为三层方案(L1公开/L2人在环/L3授权账号默认关)；强风控平台优先官方API不用账号爬。
- **FB-5 数据质量**：定为来源分级+定性转量化(老板打定性标签/黑名单，系统量化)+多源交叉+忠实度校验。
- **优先级**：先建 Ingestion 层(FB-8)作为工厂第一个新增通用能力。

### 文件影响
- **新增**：docs/research/data-acquisition-feasibility.md（取数+数据质量可行性评估）
- **改动**：projects/debt-collection/docs/DISCOVERY.md（要点2/3 调研结论）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-5/FB-6 状态）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 12 轮] 2026-06-11

### 需求变动
- **实现**：FB-8 工厂通用 Ingestion 层（多格式→结构化）。
- **新增**：data-ingestion / data-quality 两个工厂 skill。
- **新增**：系统调研产出的 sources.yaml 初版（老板后续微调共同维护）。

### 文件影响
- **新增**：_factory/patterns/ingestion-pipeline/（models/processors/pipeline/cli + tests + README + pyproject）
- **新增**：_factory/skills/data-ingestion.skill.md、_factory/skills/data-quality.skill.md
- **新增**：projects/debt-collection/sources.yaml（数据源可信度初版）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-8✅ + 新增能力节）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

### 说明
- 工厂首次完成"调研→落地通用能力"闭环。数据源/质量按老板要求重点对待。

---

## [第 13 轮] 2026-06-11

### 需求变动（老板三件）
- **实现**：FB-6 取数层 L1（官方公开渠道合规取数协调器，不爬不封号）。
- **新增**：sources.yaml 系统审阅建议（拉黑标准/评级原则）。
- **新增**：Ingestion 真机验证脚本（老板装库后验真实解析）。

### 文件影响
- **新增**：_factory/patterns/data-acquisition/（registry/models/planner/cli + tests + README + pyproject）
- **新增**：_factory/skills/data-acquisition.skill.md
- **新增**：_factory/patterns/ingestion-pipeline/verify-real.sh
- **改动**：projects/debt-collection/sources.yaml（审阅建议+黑名单填法）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-6 L1✅）、DEV_LOG/CHANGELOG/PROJECT_STATE

### 说明
- 取数层坚持"协调器而非爬虫"，落实账号安全+合规硬约束。

---

## [第 14 轮] 2026-06-11

### 需求变动
- **修复**：Ingestion 处理器从"占位"改为"真实调用"(MarkItDown/FunASR/MinerU/pypdf)；空内容问题解决。
- **实现**：FB-6 L2 浏览器辅助(人在环)——browser-use 接 GLM，遇验证码/登录停下等人工。
- **改进**：跳过 .DS_Store 等垃圾文件；markitdown 安装提示改 [all]。

### 文件影响
- **改动**：_factory/patterns/ingestion-pipeline/src/ingestion/processors.py（真实接入重写）、pipeline.py（跳垃圾文件）、verify-real.sh、pyproject、tests
- **新增**：_factory/patterns/data-acquisition/src/acquisition/browser_assist.py（L2）
- **改动**：data-acquisition 的 cli.py(--l2)、tests、README、data-acquisition.skill.md
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md、docs/FACTORY_ASSESSMENT.md

---

## [第 15 轮] 2026-06-12

### 需求变动
- **新增**：真机安装指南 SETUP_GUIDE.md(MinerU/FunASR torch/browser-use 模型选型)。
- **新增**：data-acquisition CLI --bu-model 切换 L2 模型。
- **产出**：debt-collection SPEC(架构+5 ADR+RISK+10任务 TASK_GRAPH)，待 HITL Gate-2。

### 文件影响
- **新增**：docs/SETUP_GUIDE.md
- **改动**：_factory/patterns/data-acquisition/src/acquisition/cli.py(--bu-model)
- **新增/改动**：projects/debt-collection/docs/{SPEC.md, RISK.md, TASK_GRAPH.md, adr/ADR-001~005}, AGENTS.md(phase)
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md、docs/FACTORY_ASSESSMENT.md

---

## [第 16 轮] 2026-06-12

### 需求变动
- **新增规则**：R1 模型选型不限本地、R2 决断前先调研主流方案(HANDOFF 0.0.1)。
- **升级**：debt-collection 从"一次性报告"→"动态案件博弈"(情报库+时间线+动态重算+合法筹码，ADR-006)。
- **修复**：MinerU 真实接入 ingestion(SDK+CLI)；根目录污染(产物移至项目 runtime/)。
- **进入 BUILD**：实现 models/ledger/timeline/intel/compliance(13 passed)。

### 文件影响
- **改动**：HANDOFF.md(R1/R2)、docs/SETUP_GUIDE.md(项目内环境+清理)、.gitignore(runtime/)
- **改动**：_factory/patterns/ingestion-pipeline/{processors.py(MinerU真实接入), verify-real.sh}
- **改动/新增**：projects/debt-collection/docs/{SPEC.md(动态升级), TASK_GRAPH.md, adr/ADR-006}
- **新增**：projects/debt-collection/{pyproject.toml, .gitignore, src/debt/{models,ledger,timeline,intel,compliance}.py, tests/test_debt.py}
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 17 轮] 2026-06-12

### 需求变动
- **新增**：浏览器工具三条腿选型(browser-use+browser-act+MediaCrawler)，社交情报源纳入。
- **完成**：BUILD 骨架搭满(knowledge/llm_client/strategy/integrations/cli)，13任务完成12。

### 文件影响
- **新增**：docs/research/browser-automation-tools-selection.md
- **新增**：projects/debt-collection/src/debt/{knowledge,llm_client,strategy,integrations,cli}.py
- **改动**：projects/debt-collection/tests/test_debt.py(18 passed)、docs/TASK_GRAPH.md
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md、docs/FACTORY_ASSESSMENT.md

---

## [第 18 轮] 2026-06-12

### 需求变动
- **新增规则 R3**：操作指示必须保姆级详细。
- **新增**：RUNBOOK_BUILD_VERIFY.md(真机验BUILD/GLM对比/工具安装 逐步)。
- **HARDEN 准备**：HARDEN_CHECKLIST.md + security_scan.sh(自检11项全过)。

### 文件影响
- **改动**：HANDOFF.md(R3)
- **新增**：docs/RUNBOOK_BUILD_VERIFY.md
- **新增**：projects/debt-collection/docs/harden/{HARDEN_CHECKLIST.md, security_scan.sh}
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 19 轮] 2026-06-12

### 需求变动
- **HARDEN 决策**：策略模型每次可选(--model)；DB 暂明文。
- **实现**：report --model 隐私/质量切换。
- **产出**：SECURITY_REVIEW.md(威胁建模,无高危,待GLM复核)。

### 文件影响
- **改动**：projects/debt-collection/src/debt/cli.py(--model)
- **改动**：projects/debt-collection/docs/harden/HARDEN_CHECKLIST.md(决策落地)
- **新增**：projects/debt-collection/docs/harden/SECURITY_REVIEW.md
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 20 轮] 2026-06-12

### 需求变动
- **新增**：RETRO 复盘模板(双视角+待真机占位) + lesson 草稿 + 真机数据一键收集脚本。

### 文件影响
- **新增**：projects/debt-collection/docs/RETRO.md
- **新增**：_factory/lessons/2026-Q2-debt-collection.lesson.md
- **新增**：projects/debt-collection/docs/collect-retro-data.sh
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 21 轮] 2026-06-12

### 需求变动
- **新增规则 R4**：所有 LLM 工作记录遥测(事件+耗时+实时计时器+JSONL储备)。
- **重构**：合规判定 v2(否定语境识别修复误判+分级+结构化整改+递归重生成)。
- **新增**：工厂 Pattern llm-telemetry。

### 文件影响
- **新增**：_factory/patterns/llm-telemetry/(telemetry.py+pyproject+README+tests)
- **改动**：HANDOFF.md(R4)
- **重构**：projects/debt-collection/src/debt/compliance.py(v2)
- **改动**：projects/debt-collection/src/debt/{strategy.py(递归整改+遥测), integrations.py(注入遥测path), cli.py(整改理由)}
- **改动**：projects/debt-collection/tests/test_debt.py(22 passed)、docs/harden/security_scan.sh(UTF-8)
- **改动**：docs/RETRO.md(真机结果)、FACTORY_ASSESSMENT.md、DEV_LOG.md、CHANGELOG.md、PROJECT_STATE.md

---

## [第 22 轮] 2026-06-12

### 需求变动
- **新增**：反封号爬取详尽调研报告(含 Higgsfield 澄清)。
- **新增**：Claude 独立策略报告样例(对比 GLM)。
- **新增**：工厂 backlog FB-10(反封号取数+数据流水线)。

### 文件影响
- **新增**：docs/research/anti-ban-crawling-strategy.md
- **新增**：projects/debt-collection/docs/strategy-sample-claude.md
- **改动**：docs/FACTORY_ASSESSMENT.md、DEV_LOG.md、CHANGELOG.md、PROJECT_STATE.md

---

## [第 23 轮] 2026-06-12

### 需求变动(方法论级)
- **新增规则 R5(调研穷尽)、R6(缺知识求助不假装)**。
- **新增工厂核心能力 FB-11：专家系统/决策大脑**(独立可复用领域专家)。
- **新增**：开源模型全景调研、专家系统设计、专家模板、工厂运转手册。

### 文件影响
- **改动**：HANDOFF.md(R5/R6)
- **新增**：docs/research/expert-system-design.md、docs/FACTORY_OPERATIONS.md
- **新增**：_factory/experts/_TEMPLATE.expert/(expert.yaml/README/knowledge/_gaps.md/_sources.yaml)
- **改动**：docs/FACTORY_ASSESSMENT.md(FB-11+方法论修正)、DEV_LOG.md、CHANGELOG.md、PROJECT_STATE.md

---

---

## [第 47 轮] 2026-06-20 — 真实模型调用首次成功（v1.2.9）

### 需求变动
- **里程碑达成**：首次通过流式 Smart Proxy 获得真实 LLM 共识报告（耗时 1132.5s）
- **核心突破**：
  - 实现 SSE 流式直通 + chunk 级超时（最终 600s）
  - 自动拉起 MTPLX 模型 + 就绪探针
  - 字段白名单过滤解决 400 Bad Request
  - 心跳保活机制（45s~60s）
- **经验教训**：
  - 对 27B 长思考模型，**必须用 streaming + chunk 超时 + 心跳**，而非单纯加大总超时
  - MTPLX 必须使用启动日志中的短 model_id（`mtplx-qwen36-27b-optimized-quality`）
  - `urllib.request` 不支持真正流式，必须改用 `httpx.stream`
  - 模型沉默思考阶段（`mtplx_stream_silence`）可达数分钟，需极高 chunk 超时

### 文件影响
- **新增**：`_infra/smart_proxy_streaming.py`（SSE 流式版）
- **重构**：`peer_review/llm_client.py`（LiteLLMBackend 改为流式）
- **新增**：`scripts/test_streaming_plan.py`、`scripts/start_streaming_proxy.sh`
- **改动**：`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/benchmark.md`

---

## [第 46 轮] 2026-06-20 — 实现 SSE 流式直通 + 心跳保活（v1.2.8）

### 需求变动
- 按专业方案实现 Smart Proxy 流式改造
- 修复 URL 重复 `/v1` 导致的 404
- 大幅放宽超时（300s → 600s chunk）

---

## [第 45 轮] 2026-06-20 — Smart Proxy 生产级优化（v1.2.7）

### 需求变动
- **Smart Proxy 核心修复**：
  - 将 `httpx` 超时从 300s 提升至 600s（read timeout）
  - 增加 3 次重试机制（带 2s 间隔）
  - 修复 `asyncio` 导入缺失问题
  - 针对 MTPLX 长思考模式做兼容优化
- **里程碑**：Smart Proxy 现在支持真实模型调用（已验证 200 OK + 400 → 200 恢复）

### 文件影响
- **改动**：`_infra/smart_proxy.py`（超时 + 重试 + 导入修复）
- **改动**：`docs/PROJECT_STATE.md`（记录 Smart Proxy 优化状态）
- **改动**：`docs/CHANGELOG.md`（新增本节）

---

## [第 44 轮] 2026-06-20 — 沙箱压测全链路打通（v1.2.6）

### 需求变动
- **里程碑执行**：在 Arena 沙箱中完整运行 benchmark_test.py
  - 成功安装 peer-review 包（含 langgraph 1.2.6 + litellm + chromadb 等全部依赖）
  - 4 个方案全部通过配置验证并执行 LangGraph 流程
  - 记录真实运行日志（Connection refused 是预期，因为无本地模型服务）
- **文档更新**：在 benchmark.md 中新增 v1.2.6 里程碑记录表

### 文件影响
- **新增执行记录**：沙箱成功运行 benchmark（4 方案全部 ✅）
- **改动**：`docs/benchmark.md`（新增 v1.2.6 压测结果表格）
- **改动**：`docs/CHANGELOG.md`（新增本节）

### 验收
- ✅ venv + editable install 成功
- ✅ benchmark 脚本完整运行（无 ConfigurationError）
- ✅ LangGraph 评审流程正常执行
- ✅ 所有方案模型引用正确

---

## [第 43 轮] 2026-06-20 — 模型压测打通（v1.2.6）

### 需求变动
- **核心修复**：解决 benchmark_test.py 启动时“模型配置不一致”错误
  - 根因：`routing_plans.yaml` 中 `full-check` 方案引用了未定义的模型 `local-fast`（节点 `fast_classify`）
  - 修复：删除 `fast_classify` 节点（该节点在代码中无实现，且其他方案均未使用）
- **全量检测**：完成对 peer-review 引擎 26 个 Python 文件的语法 + 导入链 + 配置交叉验证
- **结果**：配置系统、节点工厂、LangGraph 构建链路全部健康（仅缺 langgraph 运行时依赖）
- **里程碑**：压测链路正式打通，`full-check` / `default` / `high-quality` / `all-local` / `mtplx-hybrid` 五方案均可正常加载

### 文件影响
- **改动**：`config/routing_plans.yaml`（移除 fast_classify + local-fast）
- **改动**：`docs/PROJECT_STATE.md`（升级到 v1.2.6，记录本次修复）
- **改动**：`docs/CHANGELOG.md`（新增本节）
- **新增**：`/home/user/test02_deploy_key` + `.pub`（用于 GitHub Deploy Key 推送）

### 验收
- ✅ `load_all_configs()` 交叉验证通过
- ✅ 所有压测方案模型引用一致
- ✅ 无残留未定义模型引用
- ✅ 代码无语法错误

---

## [第 37 轮] 2026-06-16（Phase 1 立即启动）

### 需求变动
- **Phase 1 治理行动**（响应 DOCUMENT_AUDIT_REPORT.md 发现的 "Missing ADR" 高优先级问题）：
  - 创建 `docs/adr/` 目录（工厂级 ADR SSOT）。
  - 新增 7 个完整工厂级 ADR（ADR-001 ~ ADR-007），覆盖 LangGraph 迁移、双文件模型、DataPrivacyGate、MTPLX 后端、KnowledgeHub 重构、forge eval、MemoryStore 作为 SSOT。
  - 每个 ADR 均遵循规范模板（Context、Alternatives、Decision、Rationale、Consequences、Risks、Rollback Strategy）。
- **文档体系强化**：
  - 新增 `docs/adr/README.md`（ADR 索引 + 阅读指南）。
  - 更新 `docs/DECISIONS.md`（标记为 legacy，指向 `docs/adr/` 作为当前 SSOT）。
  - 更新 `docs/PROJECT_STATE.md`（清理重复段落，建立清晰 SSOT 结构）。
  - 更新 `DOCUMENT_AUDIT_REPORT.md`（记录 Phase 1 进展）。
- **持续治理**：正式将 "创建/更新根级别 ADR" 纳入变更流程。

### 文件影响
- **新增**：`docs/adr/ADR-001-langgraph-migration.md` ~ `ADR-007-memorystore-as-plan-comparison-ssot.md`（7 个文件） + `docs/adr/README.md`
- **改动**：`docs/DECISIONS.md`、`docs/PROJECT_STATE.md`、`DOCUMENT_AUDIT_REPORT.md`、`docs/CHANGELOG.md`
- **Git 推送**：已完成（commit bbfd0eb）

**Phase 1 核心目标达成**：根目录工厂级 ADR 缺失问题已解决。

---

## [第 36 轮] 2026-06-16

### 需求变动
- **重大治理行动**：执行用户提供的 Documentation Governance & Audit 完整规范，进行第一次系统性项目审计。
- **新增**：`DOCUMENT_AUDIT_REPORT.md`（结构化审计报告，覆盖 6 大维度：Consistency、Stale、Coverage、SSOT、ADR、Drift）
- **新增**：`DOCUMENT_CHANGE_REPORT.md`（本次变更记录 + 风险与后续）
- **识别问题**（高优先级）：
  - 大量文档漂移（尤其是 4-Final Architecture Design.md 与实际 v1.1.0 实现）
  - HANDOFF.md 仍保留已废止的 ZIP 补丁流程（Phase 1 已彻底清理并移除所有引用）
  - 根目录严重缺失工厂级 ADR（SSOT 碎片化）
  - PROJECT_STATE.md 存在重复内容
  - 孤立文档与孤立代码（早期 research + Agno 遗留模块）
- **输出**：清晰的 Phase 1/2/3 治理修复计划 + 正式启动 Continuous Governance 机制。
- **原则强化**：文档现在被视为与代码同等优先级的交付物（Code → Tests → Documentation → CHANGELOG → ADR）。

### 文件影响
- **新增**：`DOCUMENT_AUDIT_REPORT.md`、`DOCUMENT_CHANGE_REPORT.md`
- **强化引用**：`docs/UPGRADE_COMPLETION.md`、`docs/PROJECT_STATE.md`
- **改动**：`docs/CHANGELOG.md`（新增本节）
- **后续行动**（Phase 1 必须完成）：
  - 创建 `docs/adr/` 目录并补齐至少 7 个工厂级 ADR
  - 重写 `HANDOFF.md`（彻底删除 ZIP 流程）
  - 清理重复内容并建立清晰 SSOT

---

## [第 29 轮 · Wave 1 + Wave 2 Task 1] 2026-06-14

### 需求变动
- **Wave 1 基础设施稳定化**：
  - 测试阻塞修复：`__init__.py` HTML 注释 → Python 注释
  - Editable Install：`pip install -e .` 成功，移除 `cli.py` 中 `sys.path.insert`
  - Git 发布流程：`Makefile` + `release.sh` (语义化版本 + CHANGELOG + git tag)
  - 数据备份自动化：`backup.sh` 每日备份 runtime/，保留 30 天
  - Baseline Benchmark：`docs/benchmark.md` 记录 MLX 基线指标
- **Wave 2 Task 1 Pydantic 配置体系 (双文件模型管理)**：
  - `config/models.yaml` (A 文件)：10 模型定义 (本地 6 + 中国 API 4)
  - `config/routing_plans.yaml` (B 文件)：5 方案 (default/high-quality/all-local/fast/manual-override)
  - `config/privacy_policy.yaml`：9 字段 × 3 端点，4 种策略类型
  - `peer_review.config.schemas`：完整 Pydantic Schema (ExpertConfig, ModelConfig, PlanConfig 等)
  - `peer_review.config.loader`：统一加载入口 `load_all_configs()`，启动时交叉验证
  - 专家 ID 强制校验格式，模板目录 `_TEMPLATE.expert` 自动跳过
  - 专家 YAML 统一引用 `local-qwen35b` (models.yaml 键名)

### 文件影响
- **新增**：`config/models.yaml`、`config/routing_plans.yaml`、`config/privacy_policy.yaml`
- **新增**：`_factory/patterns/peer-review/src/peer_review/config/{schemas.py, loader.py, __init__.py}`
- **新增**：`Makefile`、`backup.sh`、`release.sh`、`docs/benchmark.md`
- **改动**：`_factory/patterns/peer-review/src/peer_review/__init__.py` (修复语法)
- **改动**：`projects/debt-collection/src/debt/cli.py` (移除 sys.path.insert)
- **改动**：4 个专家 YAML (统一 model 键名)
- **改动**：`HANDOFF.md` (发布流程、CLI 使用方式)、`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`
- **Git 标签**：`v1.1.0-wave1-complete` 已推送

### 验收
- `make test` 全通过 (verify_architecture + 22 debt tests)
- 配置加载成功：10 模型、5 方案、4 专家
- 交叉验证通过 (A/B 文件一致性、专家引用检查)
- CLI 正常运行：`debt review 1 --model local/primary`

---

## [2026-06-22] E5 Privacy Gateway — PIIDetector ABC (E5-C3-S1-T1)

### Added
- `PIIDetector` abstract base class in `_infra/network/privacy_gateway/detectors/base.py`
  - `async def detect(self, text: str) -> List[PIIEntity]`
  - `get_name()`, `health_check()`, `supports_type()`
- Supporting models already in place: `PIIType` (Enum), `PIIEntity` (Pydantic + `mask()`)
- `detectors/__init__.py` and cleaned `__init__.py` exports
- Unit tests: `test_pii_detector.py` (16 tests covering ABC enforcement, model validation, dummy implementation)

### Changed
- Restored historical content in `docs/DEV_LOG.md` and `docs/CHANGELOG.md`
- Appended new round records (append-only, no overwrite)

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_pii_detector.py -q
# 16 passed
python -m pytest _infra/network/tests/unit/ -q
# 113+ passed
```


---

## [2026-06-22] E5 Privacy Gateway — E5-C3 状态收敛与导入隔离修复

### Fixed
- 修复 `_infra/network/privacy_gateway/detectors/__init__.py` 提前导入 `PresidioDetector` 导致 `PIIDetector` ABC 测试依赖 `presidio_analyzer` 的问题。
- `_infra/network/privacy_gateway/__init__.py` 现在安全导出 `PIIDetector / PIIType / PIIEntity`，不触发 Presidio 可选依赖加载。
- `test_presidio_detector.py` 与 `test_cn_recognizers.py` 增加可选依赖门控，最小沙箱未安装 `presidio_analyzer` 时跳过而非 collection error。

### Changed
- `TASK_BACKLOG.md` 以源码为准同步 E5-C3 状态：
  - `E5-C3-S1-T1` / `T2` / `T3` 标记完成。
  - `E5-C3-S1-T4` 保持 TODO，作为下一候选任务。
  - E5-C4 ~ E5-C9 的详细 DoD 恢复为未完成状态，避免文档误报。
- `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`_infra/network/README.md` 同步当前真实进度。
- 本轮修改的 E5-C3 源码和测试文件补齐 LLM 留痕头部。

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_pii_detector.py -q
# 17 passed
python -m pytest _infra/network/tests/unit/ -q
# 115 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- `presidio_analyzer` 未安装的最小沙箱会跳过 Presidio / 中文 recognizer 真实行为测试；真机完整验证需安装该依赖。
- 下一建议任务：`E5-C3-S1-T4` Token / API Key Recognizers。

---

## [2026-06-22] E5 Privacy Gateway — Token / API Key Recognizers (E5-C3-S1-T4)

### Added
- `_infra/network/privacy_gateway/recognizers/secret_recognizers.py`
  - deterministic `detect_secrets()` scanner
  - optional Presidio `get_secret_recognizers()` factory
- `_infra/network/tests/unit/test_secret_recognizers.py` with 12 unit tests.
- New `PIIType` values:
  - `SESSION_ID`
  - `COOKIE`
  - `OAUTH_TOKEN`

### Changed
- `PresidioDetector` now registers secret recognizers when Presidio is available.
- `PRESIDIO_TO_PII_TYPE` now maps API_KEY / ACCESS_TOKEN / JWT / PRIVATE_KEY / SESSION_ID / COOKIE / OAUTH_TOKEN.
- `TASK_BACKLOG.md` marks `E5-C3-S1-T4` as done and sets the next TODO to `E5-C4-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_secret_recognizers.py -q
# 12 passed
python -m pytest _infra/network/tests/unit/test_pii_detector.py -q
# 17 passed
python -m pytest _infra/network/tests/unit/ -q
# 127 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Presidio-specific recognizer runtime path remains skipped in sandbox without `presidio_analyzer`; full local validation should run on the user's Python environment with Presidio installed.
- Next recommended task: `E5-C4-S1-T1` SpaCyNERDetector.

---

## [2026-06-22] E5 Privacy Gateway — SpaCyNERDetector (E5-C4-S1-T1)

### Added
- `_infra/network/privacy_gateway/detectors/ner_detector.py`
  - `SpaCyNERDetector`
  - `SPACY_LABEL_TO_PII_TYPE`
  - zh/en model selection with graceful degradation
- `_infra/network/scripts/download_spacy_models.py`
  - downloads `zh_core_web_sm` and `en_core_web_sm` by default
- `_infra/network/tests/unit/test_ner_detector.py`
  - 7 dependency-injected unit tests, no real model download required

### Changed
- `_infra/network/privacy_gateway/detectors/__init__.py` lazy-loads `SpaCyNERDetector`.
- `TASK_BACKLOG.md` marks `E5-C4-S1-T1` as done and sets the next TODO to `E5-C5-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_ner_detector.py -q
# 7 passed
python -m pytest _infra/network/tests/unit/ -q
# 134 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Full real-model validation requires downloading spaCy models on the user's machine:
  `python _infra/network/scripts/download_spacy_models.py`
- Next recommended task: `E5-C5-S1-T1` QwenPIIClassifier.

---

## [2026-06-22] E5 Privacy Gateway — QwenPIIClassifier (E5-C5-S1-T1)

### Added
- `_infra/network/privacy_gateway/detectors/qwen_classifier.py`
  - `QwenPIIClassification` (`yes` / `no` / `uncertain`)
  - `QwenPIIResult`
  - `QwenPIIClassifier`
- `_infra/network/tests/unit/test_qwen_classifier.py`
  - 10 fake-client unit tests with no real Ollama dependency

### Changed
- `_infra/network/privacy_gateway/detectors/__init__.py` lazy-loads `QwenPIIClassifier`.
- `TASK_BACKLOG.md` marks `E5-C5-S1-T1` as done and sets the next TODO to `E5-C6-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_qwen_classifier.py -q
# 10 passed
python -m pytest _infra/network/tests/unit/ -q
# 144 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Full local integration requires Ollama service and qwen3:8b:
  `ollama pull qwen3:8b`
- Next recommended task: `E5-C6-S1-T1` PIIReplacer.

---

## [2026-06-22] E5 Privacy Gateway — PIIReplacer (E5-C6-S1-T1)

### Added
- `_infra/network/privacy_gateway/replacer.py`
  - `PIIReplacer`
  - `PIIReplacementResult`
  - `PIIPlaceholderMapping`
  - `InMemoryPIIMapStore`
- `_infra/network/tests/unit/test_pii_replacer.py`
  - 9 unit tests for replacement, same-value reuse, mapping query, overlap handling, custom placeholder format

### Changed
- `_infra/network/privacy_gateway/__init__.py` exports PIIReplacer and related mapping models.
- `TASK_BACKLOG.md` marks `E5-C6-S1-T1` as done and sets the next TODO to `E5-C6-S1-T2`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_pii_replacer.py -q
# 9 passed
python -m pytest _infra/network/tests/unit/ -q
# 153 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- SQLCipher encrypted persistence is intentionally deferred to `E5-C6-S1-T2`.
- Next recommended task: `E5-C6-S1-T2` SQLCipher PII Map DB.

---

## [2026-06-22] E5 Privacy Gateway — PII Map DB (E5-C6-S1-T2)

### Added
- `_infra/network/privacy_gateway/pii_map_db.py`
  - `PIIMapDB`
  - `AES256FieldCipher`
  - SQLCipher driver preference with sqlite3 field-level encrypted fallback
- `_infra/network/scripts/init_pii_map_db.py`
  - initializes encrypted `runtime/pii_map.db`
  - supports `--require-sqlcipher`
- `_infra/network/tests/unit/test_pii_map_db.py`
  - 8 tests covering CRUD, wrong-key failure, plaintext absence, schema creation, require_sqlcipher behavior

### Changed
- `_infra/network/privacy_gateway/__init__.py` exports PIIMapDB / PIIMapDBConfig / PIIMapDecryptionError.
- `TASK_BACKLOG.md` marks `E5-C6-S1-T2` as done and sets next TODO to `E5-C7-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_pii_map_db.py -q
# 8 passed
python -m pytest _infra/network/tests/unit/ -q
# 161 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
PII_MAP_ENCRYPTION_KEY=test-key-at-least-16-chars python _infra/network/scripts/init_pii_map_db.py --db /tmp/test02_pii_map_check.db
# initialized
```

### Known Follow-up
- For file-level SQLCipher in production, install a SQLCipher Python binding and run with `--require-sqlcipher`.
- Next recommended task: `E5-C7-S1-T1` JSON Schema output validator.

---

## [2026-06-22] E5 Privacy Gateway — JSON Schema Output Validator (E5-C7-S1-T1)

### Added
- `config/output_schemas/privacy_gateway_output.schema.yaml`
  - strict Draft 2020-12 schema for redacted Privacy Gateway output
  - forbids raw PII `value` inside `entities`
- `_infra/network/privacy_gateway/validator.py`
  - `PrivacyOutputValidator`
  - `validate_privacy_output()`
  - `safe_entity_metadata()`
  - `build_privacy_output()`
- `_infra/network/tests/unit/test_privacy_output_validator.py`
  - 10 unit tests covering valid output, invalid output, raw-value rejection, schema loading and safe helper behavior

### Changed
- `_infra/network/privacy_gateway/__init__.py` exports output validator helpers.
- `TASK_BACKLOG.md` marks `E5-C7-S1-T1` as done and sets next TODO to `E5-C8-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_privacy_output_validator.py -q
# 10 passed
python -m pytest _infra/network/tests/unit/ -q
# 171 passed, 2 skipped, 3 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E5-C8-S1-T1` CanaryTokenMonitor.

---

## [2026-06-22] E5 Privacy Gateway — CanaryTokenMonitor (E5-C8-S1-T1)

### Added
- `_infra/network/privacy_gateway/canary.py`
  - `CanaryTokenMonitor`
  - `CanaryHit`
  - config-driven token / wildcard / regex matching
  - immediate blocking via `CanaryTokenDetectedError`
  - optional masked audit logging
- `config/canary_tokens.yaml`
  - default `AI_CANARY_DO_NOT_LEAK_2026`
- `_infra/network/tests/unit/test_canary_monitor.py`
  - 8 tests covering detection, blocking, wildcard, config loading, masked audit and sorting

### Changed
- `_infra/network/privacy_gateway/__init__.py` exports CanaryTokenMonitor / CanaryHit.
- `TASK_BACKLOG.md` marks `E5-C8-S1-T1` as done and sets next TODO to `E5-C9-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_canary_monitor.py -q
# 8 passed
python -m pytest _infra/network/tests/unit/ -q
# 179 passed, 2 skipped, 4 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E5-C9-S1-T1` PrivacyGateway orchestration pipeline.

---

## [2026-06-22] E5 Privacy Gateway — PrivacyGateway Pipeline (E5-C9-S1-T1)

### Added
- `_infra/network/privacy_gateway/gateway.py`
  - `PrivacyContext`
  - `RedactedContent`
  - `PrivacyGateway`
  - `process()` / `process_text()`
- `_infra/network/tests/unit/test_privacy_gateway.py`
  - 8 integration-style unit tests covering L1-L7 orchestration and failure handling

### Changed
- `_infra/network/privacy_gateway/__init__.py` exports PrivacyGateway / PrivacyContext / RedactedContent.
- `TASK_BACKLOG.md` marks `E5-C9-S1-T1` as done and keeps `E5-C9-S1-T2` as next TODO.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_privacy_gateway.py -q
# 8 passed
python -m pytest _infra/network/tests/unit/ -q
# 187 passed, 2 skipped, 4 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E5-C9-S1-T2` build_privacy_gateway factory function.

---

## [2026-06-22] E5 Privacy Gateway — build_privacy_gateway Factory (E5-C9-S1-T2)

### Added
- `build_privacy_gateway(config=None, ...)` in `_infra/network/privacy_gateway/gateway.py`
  - reads `config/network.yaml` when config is omitted
  - supports `NetworkConfig` or mapping input
  - wires detectors, Qwen classifier, replacer, PII map store, validator, canary monitor

### Changed
- `_infra/network/privacy_gateway/__init__.py` exports `build_privacy_gateway`.
- `_infra/network/tests/unit/test_privacy_gateway.py` adds factory tests.
- `TASK_BACKLOG.md` marks `E5-C9-S1-T2` as done; E5 Privacy Gateway MVP is now complete.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_privacy_gateway.py -q
# 10 passed
python -m pytest _infra/network/tests/unit/ -q
# 189 passed, 2 skipped, 4 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- E5 Privacy Gateway MVP is complete but not yet wired into NetworkWorkflow / CLI flows.
- Recommended next tasks: M3 security tests (E11-C2/E11-C4/E11-C6) or workflow integration, depending on user priority.

---

## [2026-06-22] Security — Prompt Injection Tests (E11-C2-S1-T1)

### Added
- `_infra/network/tests/security/test_prompt_injection.py`
  - 12 security tests covering hidden instructions, display:none, visibility:hidden, HTML comments, Unicode full-width obfuscation, URL encoding and tool-call triggers
- Malicious HTML fixtures under `_infra/network/tests/fixtures/malicious_pages/`

### Changed
- `_infra/network/input_sanitizer/sanitizer.py`
  - runs NFKC + URL decode before injection detection
  - removes hidden HTML blocks before token-level stripping
  - strips tool-trigger hints (`execute_js`, `document.cookie`, storage access, `rm -rf /`)
- `TASK_BACKLOG.md` marks `E11-C2-S1-T1` as done and sets next TODO to `E11-C4-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/security/test_prompt_injection.py -q
# 12 passed
python -m pytest _infra/network/tests/unit/test_input_sanitizer.py -q
# 8 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 201 passed, 2 skipped, 4 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E11-C4-S1-T1` PII bypass security tests.

---

## [2026-06-22] Security — PII Bypass Tests (E11-C4-S1-T1)

### Added
- `_infra/network/privacy_gateway/recognizers/pii_recognizers.py`
  - deterministic CN phone / email / CN ID / Luhn bank card / Base64-encoded PII detection
- `_infra/network/tests/security/test_pii_bypass.py`
  - 11 security tests covering Unicode homoglyphs, zero-width, Base64, URL encoding, separators, table split, JSON key/value, code variable hiding and schema-safe output

### Changed
- `_infra/network/privacy_gateway/gateway.py`
  - L2 now includes deterministic common PII recognizers in addition to optional Presidio and secret regex recognizers
- `TASK_BACKLOG.md` marks `E11-C4-S1-T1` as done and sets next TODO to `E11-C6-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/security/test_pii_bypass.py -q
# 11 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 212 passed, 2 skipped, 4 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E11-C6-S1-T1` Canary Token end-to-end test.

---

## [2026-06-22] Security — Canary Token E2E Tests (E11-C6-S1-T1)

### Added
- `_infra/network/tests/security/test_canary_e2e.py`
  - 7 end-to-end style tests covering canary in search result, extracted markdown, browser page, privacy output, mixed PII+canary, masked audit logging, and clean pass

### Changed
- `TASK_BACKLOG.md` marks `E11-C6-S1-T1` as done; M3 Privacy Gateway + security tests are complete.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/security/test_canary_e2e.py -q
# 7 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 219 passed, 2 skipped, 5 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- M3 is complete; next backlog milestone is M4 MCP security governance, or NetworkWorkflow/CLI integration if prioritized.

---

## [2026-06-22] MCP Guard — Pinned MCP Install Script (E2-C1-S1-T1)

### Added
- `_infra/network/scripts/install_mcp.sh`
  - pinned git clone + exact commit checkout
  - lockfile-based dependency install
  - mcp-scan admission by default
  - writes `config/mcp_lockfile.yaml`
- `config/mcp_lockfile.yaml`
- `_infra/network/tests/unit/test_mcp_install_script.py`
  - 3 tests covering clone/checkout/lockfile and rejection of unsafe inputs

### Changed
- `.gitignore` ignores local `mcp-servers/` checkouts.
- `TASK_BACKLOG.md` marks `E2-C1-S1-T1` as done and sets next TODO to `E2-C2-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_install_script.py -q
# 3 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 222 passed, 2 skipped, 5 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E2-C2-S1-T1` mcp-scan integration and scanner output parsing.

---

## [2026-06-23] MCP Guard — mcp-scan Integration (E2-C2-S1-T1)

### Added
- `_infra/network/mcp_guard/scanner.py`
  - `MCPScanFinding`
  - `MCPScanReport`
  - `MCPScanRunner`
  - tolerant `parse_mcp_scan_output()` parser
- `_infra/network/scripts/scan_mcp.sh`
- `_infra/network/scripts/scan-mcp.sh`
- `_infra/network/tests/unit/test_mcp_scanner.py`
  - 7 tests covering parser, nested findings, process failure, lockfile paths, CLI from-json behavior

### Changed
- `TASK_BACKLOG.md` marks `E2-C2-S1-T1` as done and sets next TODO to `E2-C3-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_scanner.py -q
# 7 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 229 passed, 2 skipped, 5 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real environment validation requires installing `mcp-scan`.
- Next recommended task: `E2-C3-S1-T1` MCP Schema Hash calculation and comparison.

---

## [2026-06-23] MCP Guard — Schema Hash Validator (E2-C3-S1-T1)

### Added
- `_infra/network/mcp_guard/schema_validator.py`
  - canonical schema JSON hashing
  - lockfile-backed schema pin store
  - tools/list extraction
  - schema mutation detection with audit DB write
- `_infra/network/tests/unit/test_mcp_schema_validator.py`
  - 6 tests covering stable hash, pin/unchanged, mutation detection, audit row and description rug-pull detection

### Changed
- `_infra/network/mcp_guard/__init__.py` exports schema validator helpers.
- `TASK_BACKLOG.md` marks `E2-C3-S1-T1` as done and sets next TODO to `E2-C4-S1-T1`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_schema_validator.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 235 passed, 2 skipped, 5 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E2-C4-S1-T1` MCP Guard core abstraction.

---

## [2026-06-23] MCP Guard — Core Abstraction (E2-C4-S1-T1)

### Added
- `_infra/network/mcp_guard/models.py`
  - `PolicyDecision`
  - `MCPToolCall`
  - `MCPToolResult`
  - `GuardDecision`
- `_infra/network/mcp_guard/guard.py`
  - `MCPGuard.check(call) -> GuardDecision`
  - schema hash verification integration
  - decision audit logging
- `_infra/network/tests/unit/test_mcp_guard.py`
  - 7 tests covering models, allow/deny/approval decisions, schema change denial, audit logging

### Changed
- `_infra/network/mcp_guard/__init__.py` exports MCPGuard and core models.
- `TASK_BACKLOG.md` marks `E2-C4-S1-T1` as done and sets next TODO to `E2-C4-S1-T2`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_guard.py -q
# 7 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 242 passed, 2 skipped, 11 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Mode policy, high-risk approval and argument validation remain separate follow-up tasks.
- Next recommended task: `E2-C4-S1-T2` mode permission policy.

---

## [2026-06-23] MCP Guard — Mode Permission Policy (E2-C4-S1-T2)

### Added
- `config/mode_policies.yaml`
  - coding / research / private mode boundaries
  - allowed/denied servers and allowed/forbidden tools
- `_infra/network/mcp_guard/mode_policy.py`
  - `ModePolicy`
  - `ModePolicyResult`
  - `ModePolicyEngine`
- `_infra/network/tests/unit/test_mcp_mode_policy.py`
  - 6 tests covering coding/browser deny, research/shell deny, private read-only, config reload and MCPGuard integration

### Changed
- `_infra/network/mcp_guard/guard.py` now applies mode policy by default.
- `_infra/network/mcp_guard/__init__.py` exports mode policy classes.
- `TASK_BACKLOG.md` marks `E2-C4-S1-T2` as done and sets next TODO to `E2-C4-S1-T3`.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.
- LLM trace headers for files touched this round use `Arena.ai Agent Mode` per user request.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_mode_policy.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 248 passed, 2 skipped, 13 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Next recommended task: `E2-C4-S1-T3` high-risk tool human approval flow.

---

## [2026-06-23] MCP Guard — High-Risk Approval + Argument Validation (E2-C4-S1-T3/T4)

### Added
- `_infra/network/mcp_guard/approval.py`
  - `HighRiskApprovalEngine`
  - strict `yes` one-shot approval
  - high-risk action detection by tool name and arguments
- `_infra/network/mcp_guard/argument_validator.py`
  - blocks dangerous JS/cookie/storage patterns
  - URL allowlist support
  - max argument length support
  - PII / secret detection in args
- `_infra/network/tests/unit/test_mcp_approval.py`
  - 6 tests
- `_infra/network/tests/unit/test_mcp_argument_validator.py`
  - 7 tests

### Changed
- `_infra/network/mcp_guard/guard.py`
  - integrates high-risk approval flow
  - integrates argument validation before approval
  - all denial/approval decisions are audited without logging raw argument values
- `_infra/network/mcp_guard/__init__.py` exports approval and argument validation classes.
- `TASK_BACKLOG.md` marks `E2-C4-S1-T3` and `E2-C4-S1-T4` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_approval.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/test_mcp_argument_validator.py -q
# 7 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 261 passed, 2 skipped, 16 warnings
python -m compileall -q _infra/network
# pass
```

### Note
- This round follows the user's updated instruction allowing multiple sequential tasks in one turn; E2-C4-S1-T4 development started only after E2-C4-S1-T3 tests passed.
- LLM trace headers use `Arena.ai Agent Mode`.

---

## [2026-06-23] Security + Mode Profiles — Cookie Leak Tests and Coding MCP Profile

### Added
- `_infra/network/tests/security/test_cookie_leak.py`
  - 9 tests covering `document.cookie`, `localStorage`, `sessionStorage`, eval/Function cookie leakage, Cookie/Set-Cookie output redaction, clean snapshot pass
- `.mcp.json.coding`
  - Coding-mode MCP profile using local pinned paths under `mcp-servers/`
  - JSON-safe `_forge_trace` metadata for LLM traceability
- `_infra/network/tests/unit/test_mcp_profiles.py`
  - 3 tests validating JSON legality, trace metadata, allowed/forbidden server boundaries and no `npx`/`uvx`/`@latest`

### Changed
- `TASK_BACKLOG.md` marks `E11-C5-S1-T1` and `E6-C1-S1-T1` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.
- LLM trace uses `Arena.ai Agent Mode`.

### Verified
```bash
python -m pytest _infra/network/tests/security/test_cookie_leak.py -q
# 9 passed
python -m pytest _infra/network/tests/unit/test_mcp_profiles.py -q
# 3 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 273 passed, 2 skipped, 22 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- `.mcp.json.coding` references local pinned paths; actual MCP servers must be installed under `mcp-servers/` via the pinned installer.
- Research/private MCP profiles still pending.

---

## [2026-06-23] Docker Deployment — SearXNG + Crawl4AI (E3-C1-S1-T1/T2, E4-C1-S1-T1)

### Added
- `docker/docker-compose.yml`
  - local-only SearXNG service on `127.0.0.1:8080`
  - local-only Crawl4AI service on `127.0.0.1:11235`
  - healthchecks and persistent Docker volumes
- `docker/searxng/settings.yml`
  - JSON format enabled
  - Google disabled
  - request timeouts configured
- `docker/README.md`
  - local start and verification instructions
- `_infra/network/tests/unit/test_docker_services.py`
  - 4 static tests for compose/settings safety properties

### Changed
- `TASK_BACKLOG.md` marks `E3-C1-S1-T1`, `E3-C1-S1-T2`, and `E4-C1-S1-T1` as done with static validation notes.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_docker_services.py -q
# 4 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 277 passed, 2 skipped, 22 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real Docker runtime verification must be run on the user's Mac, because the current sandbox has no Docker binary.
- Next recommended task: `E6-C1-S1-T2` Research MCP profile.

---

## [2026-06-23] Mode Profiles — Research MCP Profile (E6-C1-S1-T2)

### Added
- `.mcp.json.research`
  - allows local pinned `searxng`, `crawl4ai`, and `playwright-public`
  - points to local-only SearXNG / Crawl4AI endpoints
  - disables private profile usage for public Playwright
  - includes JSON-safe `_forge_trace` metadata

### Changed
- `_infra/network/tests/unit/test_mcp_profiles.py`
  - adds research profile JSON validation and security boundary checks
- `TASK_BACKLOG.md` marks `E6-C1-S1-T2` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_mcp_profiles.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 280 passed, 2 skipped, 22 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Private MCP profile depends on Chrome DevTools MCP / private profile setup (E8-C1/E8-C2).

---

## [2026-06-23] Private Access — Chrome DevTools MCP Metadata + Private Profile + Private MCP Profile

### Added
- `.mcp.json.private`
  - exposes only `chrome-devtools-private`
  - includes `--browser-url=http://127.0.0.1:9222`, `--no-usage-statistics`, `--no-performance-crux`
- `_infra/network/scripts/start_private_chrome.sh`
- `scripts/start-private-chrome.sh`
- `profiles/README.md`
- `profiles/ai-private-github/README.md`
- `_infra/network/tests/unit/test_private_profile.py`

### Changed
- `config/mcp_lockfile.yaml`
  - added pinned ChromeDevTools/chrome-devtools-mcp metadata at commit `0cafee074cc4947f5672f71cb2f50dec863caa3e`
- `TASK_BACKLOG.md` marks E8-C1-S1-T1, E8-C2-S1-T1, E8-C2-S1-T2 and E6-C1-S1-T3 as done with static validation caveats.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_private_profile.py -q
# 4 passed
python -m pytest _infra/network/tests/unit/test_mcp_profiles.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 284 passed, 2 skipped, 22 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- User Mac must run pinned MCP install and mcp-scan for actual Chrome DevTools MCP checkout.
- User Mac must run private Chrome script for real browser validation.

---

## [2026-06-23] Mode Integration — switch-mode + PreToolUse Hook (E6-C2-S1-T1, E6-C3-S1-T1)

### Added
- `scripts/switch-mode.sh`
  - switches `.mcp.json` symlink between coding / research / private profiles
- `_infra/network/tests/unit/test_switch_mode.py`
  - 3 tests for symlink switching, current status, invalid mode handling
- `_infra/network/mcp_guard/hooks/pre_tool_use.py`
  - stdin JSON parser + MCPGuard invocation + JSON allow/deny output
- `scripts/hooks/pre_tool_use.sh`
  - shell wrapper for Claude Code hook integration
- `_infra/network/tests/unit/test_pre_tool_use_hook.py`
  - 5 tests for parser aliases, allow/deny decisions and shell wrapper behavior

### Changed
- `TASK_BACKLOG.md` marks `E6-C2-S1-T1` and `E6-C3-S1-T1` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_switch_mode.py -q
# 3 passed
python -m pytest _infra/network/tests/unit/test_pre_tool_use_hook.py -q
# 5 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 292 passed, 2 skipped, 24 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real Claude Code hook field names may require adding aliases; parser is intentionally tolerant.
- Recommended next task: `E8-C3-S1-T1` ChromeDevToolsMCPClient or E7 Playwright client tasks.

---

## [2026-06-23] Private Access — ChromeDevToolsMCPClient + PrivateAccessPipeline (E8-C3/E8-C4)

### Added
- `_infra/network/browser/chrome_devtools_client.py`
  - guarded Chrome DevTools MCP client boundary
  - read-only page text / network logs helpers
  - screenshot approval path
  - storage access forbidden
- `_infra/network/browser/private_pipeline.py`
  - private page text → InputSanitizer → PrivacyGateway full mode → schema-safe redacted output
  - optional audit logging without raw PII
- `_infra/network/tests/unit/test_chrome_devtools_client.py`
  - 5 tests
- `_infra/network/tests/unit/test_private_pipeline.py`
  - 4 tests

### Changed
- `_infra/network/browser/__init__.py` exports browser/private pipeline components.
- `_infra/network/mcp_guard/approval.py` treats screenshot as high-risk.
- `config/mode_policies.yaml` allows private read-only `get_network_logs` and gated `screenshot`.
- `TASK_BACKLOG.md` marks `E8-C3-S1-T1` and `E8-C4-S1-T1` as done with real-machine validation caveat.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_chrome_devtools_client.py -q
# 5 passed
python -m pytest _infra/network/tests/unit/test_private_pipeline.py -q
# 4 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 301 passed, 2 skipped, 30 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real Chrome DevTools MCP integration requires user Mac runtime validation.
- Next recommended task: E7 Playwright MCP installation/client or E10 ops scripts.

---

## [2026-06-23] Browser Automation — Playwright MCP Client + AI-Public Profile (E7-C1/C2/C3)

### Added
- `_infra/network/browser/playwright_client.py`
  - guarded Playwright MCP client facade with navigate/snapshot/click/type/wait/close
- `_infra/network/browser/profile_manager.py`
  - browser profile config reader and directory manager
- `_infra/network/tests/unit/test_playwright_client.py`
  - 6 tests
- `_infra/network/tests/unit/test_profile_manager.py`
  - 6 tests
- `profiles/ai-public/README.md`

### Changed
- `config/mcp_lockfile.yaml`
  - added pinned microsoft/playwright-mcp metadata at commit `0f4e6ff6be93c63af843c3d67894d83b37ae27a3`
  - pinned package version `@playwright/mcp@0.0.76`
- `.mcp.json.research`
  - updated playwright-public local path and startup args
- `_infra/network/browser/__init__.py` exports Playwright and profile manager components.
- `profiles/README.md` lists active public/private profiles.
- `TASK_BACKLOG.md` marks E7-C1-S1-T1, E7-C2-S1-T1, E7-C3-S1-T1 and E7-C3-S1-T2 as done with real-machine validation caveat.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_playwright_client.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/test_profile_manager.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 313 passed, 2 skipped, 38 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real Playwright MCP install/mcp-scan/browser validation must run on the user's Mac.
- Next recommended task: E7-C2-S1-T2 PlaywrightOrchestrator or E7-C4-S1-T1 SessionDetector.

---

## [2026-06-23] Browser Automation — SessionDetector + PlaywrightOrchestrator (E7-C4, E7-C2-S1-T2)

### Added
- `config/session_keywords.yaml`
- `_infra/network/browser/session_detector.py`
  - detects login / CAPTCHA / 2FA / verification pages
  - supports snapshot dict input and injected notifier
- `_infra/network/browser/playwright_orchestrator.py`
  - `go_and_extract()` public browsing flow
  - profile selection via ProfileManager
  - session detection before returning extracted text
- `_infra/network/tests/unit/test_session_detector.py`
  - 6 tests
- `_infra/network/tests/unit/test_playwright_orchestrator.py`
  - 4 tests

### Changed
- `_infra/network/browser/__init__.py` exports SessionDetector and PlaywrightOrchestrator.
- `TASK_BACKLOG.md` marks `E7-C4-S1-T1` and `E7-C2-S1-T2` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_session_detector.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/test_playwright_orchestrator.py -q
# 4 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 323 passed, 2 skipped, 44 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real Playwright MCP integration requires user Mac runtime validation.
- Recommended next task: E7-C5 action risk classifier or E7-C6 Playwright CLI wrapper.

---

## [2026-06-23] Browser Automation — Action Classifier + Playwright CLI Wrapper (E7-C5/E7-C6)

### Added
- `_infra/network/browser/action_classifier.py`
  - read_only / low_risk / high_risk classification
  - high-risk detection from action type, target and payload hints
  - safe diff_preview without raw payload
- `_infra/network/scripts/run_playwright_action.py`
  - restricted wrapper for open/snapshot/click/type/wait/close
  - argument validation and dry-run JSON plan
- `scripts/run_playwright_action.py`
  - root wrapper
- `_infra/network/tests/unit/test_action_classifier.py`
  - 6 tests
- `_infra/network/tests/unit/test_playwright_cli_wrapper.py`
  - 6 tests

### Changed
- `_infra/network/browser/__init__.py` exports action classifier.
- `TASK_BACKLOG.md` marks `E7-C5-S1-T1` and `E7-C6-S1-T1` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_action_classifier.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/test_playwright_cli_wrapper.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 335 passed, 2 skipped, 44 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real Playwright CLI wrapper execution requires the pinned local runner to be installed under `mcp-servers/playwright-public`.
- Recommended next tasks: E10 health-check / backup operational scripts.

---

## [2026-06-23] Operations — Health Check + Backup Scripts (E10-C1/E10-C3)

### Added
- `scripts/health-check.sh`
  - static config/file checks via `--static`
  - runtime service checks for SearXNG, Crawl4AI, Ollama models and selected DBs
- `scripts/backup.sh`
  - allowlist backup for `.mcp.json*`, `config/`, `docker/`, and selected runtime DBs
  - excludes profiles/cookies/sessions/password/payment data
  - supports `--dry-run` and `--dest`
- `_infra/network/tests/unit/test_ops_scripts.py`
  - 3 tests covering health static mode, backup dry-run, backup archive exclusion safety

### Changed
- `TASK_BACKLOG.md` marks `E10-C1-S1-T1` and `E10-C3-S1-T1` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_ops_scripts.py -q
# 3 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 338 passed, 2 skipped, 44 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Full runtime health requires Docker/Ollama services on the user's Mac.
- Add future DBs to backup allowlist explicitly when introduced.

---

## [2026-06-23] Operations — launchd Health and MCP Scan Jobs (E10-C2-S1-T1)

### Added
- `scripts/launchd/com.network-agent.health.plist`
  - runs `scripts/health-check.sh` every 5 minutes
  - appends logs to `runtime/logs/launchd-health.log`
- `scripts/launchd/com.network-agent.mcp-scan.plist`
  - runs weekly Sunday 03:00
  - appends logs to `runtime/logs/launchd-mcp-scan.log`
- `scripts/launchd/README.md`
  - install/uninstall instructions for macOS launchd
- `_infra/network/tests/unit/test_launchd_plists.py`
  - 3 static plist tests

### Changed
- `TASK_BACKLOG.md` marks `E10-C2-S1-T1` as done.
- `docs/PROJECT_STATE.md`, `docs/DEV_LOG.md`, `_infra/network/README.md` synchronized to current source state.

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_launchd_plists.py -q
# 3 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 341 passed, 2 skipped, 44 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- Real `launchctl load` validation must run on the user's macOS machine.

---

## [2026-06-23] Local RAG — SQLite Schema, Embedder, Store, Search (E9-C1~C4)

### Added
- `_infra/network/local_rag/schema.sql`
- `_infra/network/local_rag/models.py`
- `_infra/network/local_rag/embedder.py`
- `_infra/network/local_rag/store.py`
- `_infra/network/scripts/init_rag_db.py`
- `_infra/network/tests/unit/test_local_rag.py`

### Implemented
- SQLite documents / chunks / embeddings / FTS / access_log schema
- BGE_M3_Embedder with Ollama-compatible API and cache
- RAGStore document add, chunking, raw_hash deduplication
- Search API with Python cosine similarity fallback over stored embeddings

### Verified
```bash
python -m pytest _infra/network/tests/unit/test_local_rag.py -q
# 6 passed
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 350 passed, 2 skipped, 44 warnings
python -m compileall -q _infra/network
# pass
```

### Known Follow-up
- sqlite-vec native KNN remains a future optimization behind the same RAGStore API.
- Real bge-m3 integration requires Ollama + bge-m3 on the user's Mac.

---

## [2026-06-23] Documentation Governance Execution

### Changed
- Rewrote `README.md`, `HANDOFF.md`, and `docs/PROJECT_STATE.md` to remove stale references and align with current Network Increment implementation.
- Added latest-state indexes to `docs/DEV_LOG.md` and `docs/CHANGELOG.md`.
- Added implementation mapping/status notes to `NETWORK_ARCHITECTURE_FINAL.md`, `NETWORK_ENGINEERING_DESIGN.md`, and `PROJECT_DOSSIER_V3.md`.
- Replaced old detailed-task `src/...` paths in `TASK_BACKLOG.md` with current `_infra/network/...` implementation paths.
- Updated Chinese docs:
  - `docs/全功能最小示例项目.md`
  - `docs/工厂使用手册.md`
  - `docs/工厂能力覆盖检查.md`
- Added `docs/research/README.md` to clarify research docs are reference-only.

### Moved
- Moved old diagnostic scripts to `scripts/diagnostics/`:
  - `scripts/benchmark_test.py` → `scripts/diagnostics/benchmark_test.py`
  - `scripts/diagnose_proxy.sh` → `scripts/diagnostics/diagnose_proxy.sh`
  - `scripts/test_single_plan.py` → `scripts/diagnostics/test_single_plan.py`
  - `scripts/test_streaming_plan.py` → `scripts/diagnostics/test_streaming_plan.py`

### Preserved by user request
- `_obsolete/` remains ignored and should not be pushed to GitHub.
- The HANDOFF model-name rule remains unchanged.
- Did not modify the historical docs explicitly excluded by the user.

### Verified
```bash
python -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 350 passed, 2 skipped, 44 warnings
python -m compileall -q _infra/network scripts/diagnostics
# pass
python -m _infra.network.cli config
# Network Config loaded successfully
```

### Added
- **mini-feos-debug-lab**: Initial version (cli.py + test_cli.py)
- **AI-Parenting-Copilot**: Initial project docs
- scripts/governance_check.py: 简化治理检查（SSOT回退template_library、R5降级为信息提示、TASK_BACKLOG支持双路径）
