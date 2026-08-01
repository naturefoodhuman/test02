<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-01 01:30:00
-->


# HANDOFF —— AI Parenting Copilot Agent 接手入口

> 本文件是 AI Parenting Copilot 项目级接手入口。只处理 `projects/AI-Parenting-Copilot/` 内的育儿系统；工厂根目录仅作为能力/治理参考，不作为本项目 backlog。

---

## 0. 必读顺序

1. `docs/HANDOFF.md`（本文件）
2. `docs/PROJECT_STATE.md`
3. `docs/TASK_BACKLOG.md`
4. `docs/ARCHITECTURE_FINAL.md`
5. `docs/ENGINEERING_DESIGN.md`
6. `docs/DEV_LOG.md` 最新轮次
7. `docs/CHANGELOG.md` 最新轮次
8. 工厂根目录 `../../../PROJECT_DOSSIER_V5.md`

不要使用项目内旧拷贝 `docs/PROJECT_DOSSIER_V5.md` 作为执行依据。

---

## 1. 项目定位

AI Parenting Copilot 是家庭私有化 AI 育儿副驾驶系统，目标是在家庭局域网 Mac 服务端 + Android App 上实现低摩擦记录、离线同步、派生状态、规则安全、告警必达与克制 AI Copilot。

项目根目录固定为：

```text
projects/AI-Parenting-Copilot/
```

Android 手机端应用位置：

```text
projects/AI-Parenting-Copilot/android/
├── src/              # React Native / TypeScript 业务与 view model 逻辑
├── android/          # Android native Gradle skeleton
├── e2e/              # Detox placeholder
├── package.json
└── README.md
```

当前 Android 仍是 skeleton/static logic；尚未完成真实 RN bridge、Gradle wrapper、APK build、真机安装与 native modules 验收。

---

## 2. 当前真实状态（截至 2026-07-31）

### 已可标记 DONE

用户 Mac 已验收 `make db-integration-test`：`5 passed, 1 warning in 3.97s`。本轮修复 `make test` 在 DB env 遗留时的隔离问题后，以下可确认 DONE：

- `APC-T001` 项目骨架
- `APC-T002` FastAPI 应用壳 / Settings / DI / common
- `APC-T003` Docker Compose / Alembic 初始化
- `APC-T004` 核心数据库 Schema 初版
- `APC-T005` 日志 / metrics / tracing / health
- `APC-T006` audit service / decorator / audit_log immutability 基础
- `APC-T007` Auth/RBAC/JWT + SQLAlchemy adapter 基础
- `APC-T008` Auth API / 设备注册 / seed_family DB+in-memory 双模式
- `APC-T009` ObservationEvent 契约 + SQLAlchemy adapter 基础
- `APC-T010` Events API create/list/correct/delete + audit + DB-backed smoke
- `APC-T018` Rule Engine kernel / loader / registry / EvidencePolicy adapter 基础
- `APC-T019` Rules Admin validate/activate/admin gate + DB-backed EvidencePolicy/audit smoke
- `APC-T024` Model Gateway Smart Proxy client / routing / FakeModelClient
- `APC-T025` Privacy Gateway adapter / PII / canary / media outbound block
- `APC-T031` Alert Repository/API create/list/ack/feedback + SQLAlchemy/audit smoke

### 代码基本完成但仍 BLOCKED 的大类

这些已有 dev/in-memory/static/fake 或 adapter 代码和测试，但还没满足完整 DoD：

- `APC-T012`：PowerSync contract/config 与 `make powersync-smoke-test` 已通过用户 Mac 复验，已 DONE。
- `APC-T012`：PowerSync contract/config 已有，真实 PowerSync 写入/同步行为待验收。
- `APC-T020`-`APC-T023`：Medication/Triage/Threshold/Vaccine/Growth pure rules + golden tests 已有；生产医学/疫苗/WHO 表审查待完成。
- `APC-T026`-`APC-T028`：SQLAlchemyMemoryStore、LocalRAG adapter、Logger shared parser 与 Orchestrator DB memory injection 已通过用户 Mac 复验，已 DONE。
- `APC-T029`：Dose Interceptor 已新增 SQLAlchemyAuditSink 与 API DB smoke 覆盖；需要用户 Mac `api-db-smoke-test` 复验后解除。
- `APC-T032/T033`：safe notification adapters、alert dispatch API 与 DB delivery receipts 已完成；需要用户 Mac `api-db-smoke-test` 复验，真实 FCM/TTS/设备凭证仍待接入。
- `APC-T030`：P0 Copilots pure/dev API 已有；等待 T029 与 Vaccine/Growth 生产审查相关阻塞。
- `APC-T032`-`APC-T036`：Notification/Escalation/Health/Scheduler dev/fake 逻辑已有；真实 FCM/TTS/device/NAS/worker 待验收。
- `APC-T037`-`APC-T044`：Camera / mmWave / Media / Export / Backup / Firmware mock/dev/skeleton 已有；真实 RTSP/ISAPI/Fregata/MQTT/PlatformIO/NAS 待验收。
- `APC-T045`-`APC-T053`：Android TS view models/static flows + native skeleton 已有；真实 RN/Gradle/APK/device/Notifee/FCM/op-sqlite/PowerSync 待验收。
- `APC-T054`-`APC-T059`：DevOps/fake/security/e2e/shadow/soak/release checklist 已有；完整真机/真实设备/长稳验证待完成。

---

## 3. 最新验证基线

沙盒验证：

```bash
cd projects/AI-Parenting-Copilot
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 150 passed, 8 deselected, 1 warning
make docs-check
make lint
make typecheck
make db-integration-test
# sandbox no DB URL: 5 skipped, 1 warning
make api-db-smoke-test
# sandbox no DB URL: 1 skipped, 1 warning
make security-test
# 5 passed
make e2e-fake-test
# 1 passed
make shadow-test
make rules-validate
```

用户 Mac 最近已验收/反馈：

```bash
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
make api-db-smoke-test
# 1 passed, 1 warning
make db-integration-test
# 修复前曾因 evidence_policy duplicate unique 失败；已在当前代码修复 activate 幂等性，需用户复验
```

---

## 4. 当前最高优先级

继续开发，不等待重设计：

1. 让用户 Mac 复验 `make api-db-smoke-test` 与 `make test`，确认 Dose Interceptor DB audit + Notification DB delivery dispatch；若通过，可解除 `APC-T029`，并推进 `APC-T032/T033` 状态。
2. `APC-T012`：PowerSync 实际配置/写入链路验收（需要用户 Mac compose 环境）。
3. Android：RN bridge / Gradle wrapper / native modules / APK build（需要 Android toolchain，可能需要用户本机验收）。
4. Notification：FCM/Notifee/FullScreenIntent 真通道与告警升级取消验收（需要 Firebase/Android 设备）。

若用户继续粘贴验证失败，先修失败，再继续上述队列。

---

## 5. 常用命令

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
make backup-dry-run
```

DB integration：

```bash
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
make infra-up
make db-migrate
make db-current
make db-integration-test
```

依赖安装规则：**uv-first**。不要假设 venv 中有 pip。`server/scripts/ensure_dev_deps.py` 会优先使用：

```bash
uv pip install --python <venv-python> -e .[dev]
```

---

## 6. 架构保护速查

必须遵守：

1. LLM 只走 Model Gateway。
2. 云端出站只走 Privacy Gateway。
3. 剂量 / 阈值 / 医疗判断只由 Rule Engine 产出。
4. 告警只走 Notification Orchestrator。
5. 所有 mutating 操作必须审计。
6. Android 离线记录不得丢失。

禁止未经用户批准改变架构、边界、调用链、基础设施、核心组件或大规模重构。

---

## 7. LLM 文件头规则

文件头必须使用当前实际可确认模型标识：

```text
创建/修改该文件的LLM大模型：gpt 5.5（示例）
创建时间（北京时间）：YYYY-MM-DD HH:MM:SS
```

JSON / JSONL 使用 `_forge_trace` 字段。

---

## 8. 上下文/项目规模管理

- 每轮优先小批量 commit + push，保证远端 main 始终可恢复。
- 每轮更新 `docs/HANDOFF.md` / `docs/DEV_LOG.md` / `docs/PROJECT_STATE.md` / `docs/TASK_BACKLOG.md`，降低后续 Agent 对长对话上下文的依赖。
- 避免一次性读取全项目大文件；继续按任务读取相关模块与测试。
- 若上下文接近上限，先提交并更新 HANDOFF，再继续。
