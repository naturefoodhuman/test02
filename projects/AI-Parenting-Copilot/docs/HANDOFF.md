<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 21:40:00
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

## 2. 当前真实状态（截至 2026-07-09）

### 已可标记 DONE

用户 Mac 已验收 `make db-integration-test` 早期 4/4 通过，随后新增 API runtime integration 仍待用户复验。当前可确认 DONE：

- `APC-T001` 项目骨架
- `APC-T002` FastAPI 应用壳 / Settings / DI / common
- `APC-T003` Docker Compose / Alembic 初始化
- `APC-T004` 核心数据库 Schema 初版
- `APC-T005` 日志 / metrics / tracing / health
- `APC-T006` audit service / decorator / audit_log immutability 基础
- `APC-T007` Auth/RBAC/JWT + SQLAlchemy adapter 基础
- `APC-T009` ObservationEvent 契约 + SQLAlchemy adapter 基础
- `APC-T018` Rule Engine kernel / loader / registry / EvidencePolicy adapter 基础
- `APC-T024` Model Gateway Smart Proxy client / routing / FakeModelClient
- `APC-T025` Privacy Gateway adapter / PII / canary / media outbound block

### 代码基本完成但仍 BLOCKED 的大类

这些已有 dev/in-memory/static/fake 或 adapter 代码和测试，但还没满足完整 DoD：

- API runtime DB wiring：已新增 request-level DB session middleware 和 API DB integration harness；最新用户验收还未复跑修复后的 `make db-integration-test`。
- Auth API / Events API / Rules Admin / Alert API：已有 DB-mode adapter 切换，仍需用户复验。
- PG NOTIFY / PowerSync：trigger/config/contract validator 已有，真实 worker/PowerSync 行为待验收。
- Normalization / State Engine：in-memory event→normalization→state dev pipeline 已有，DB worker/upsert 待验收。
- Rule domains：Medication/Triage/Threshold/Vaccine/Growth pure rules + golden tests 已有；生产医学/疫苗/WHO 表审查待完成。
- Memory / Copilots / Orchestrator / Dose Interceptor：pure/dev API 已有；真实 memory/RAG/audit integration 待完成。
- Notification / Alert / Escalation / Health / Scheduler：dev/fake 逻辑已有；真实 FCM/TTS/device/NAS/worker 待验收。
- Camera / mmWave / Media / Export / Backup / Firmware：mock/dev/skeleton 已有；真实 RTSP/ISAPI/Fregata/MQTT/PlatformIO/NAS 待验收。
- Android：TS view models/static flows + native skeleton 已有；真实 RN/Gradle/APK/device/Notifee/FCM/op-sqlite/PowerSync 待验收。

---

## 3. 最新验证基线

沙盒验证（无外部 DB URL）：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped
make security-test
# 5 passed
make e2e-fake-test
# 1 passed
make shadow-test
make rules-validate
```

用户 Mac 最近已验收过：

```bash
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
make infra-up
make db-migrate
make db-current
make db-integration-test
# 曾通过 4 passed；之后新增 API runtime integration 修复，需复验到 5 passed。
```

---

## 4. 当前最高优先级

### 立即需要用户复验

本轮最后修复了 API DB runtime integration 的 transaction isolation / audit wiring。下一 Agent 应要求用户运行：

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory/projects/AI-Parenting-Copilot
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
make infra-up
make db-migrate
make db-current
make db-integration-test
```

预期：

```text
5 passed
```

若通过，可考虑解除更多 DB-backed API runtime / audit 相关 BLOCKED；若失败，先修失败。

### 如继续开发且暂不等复验

优先做：

1. DB-backed API smoke target：`make api-db-smoke-test`，覆盖真实 HTTP + DB 的 auth/event/alert/rule/state。
2. Android Gradle wrapper / RN bridge / native modules（需要 Android toolchain，可能很快需要用户验收）。
3. PowerSync real config validation / worker wiring（需要真实 PowerSync）。
4. FCM/Notifee/FullScreenIntent native implementation（需要 Firebase/Android device）。

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
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：YYYY-MM-DD HH:MM:SS
```

JSON / JSONL 使用 `_forge_trace` 字段。不要把“Execution Lead Engineer”等角色名写成模型名。
