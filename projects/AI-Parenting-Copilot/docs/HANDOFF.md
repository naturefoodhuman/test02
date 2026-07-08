<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-09 05:55:00
-->


# HANDOFF —— AI Parenting Copilot Agent 接手入口

> 本文件是 AI Parenting Copilot 项目级接手入口。任何新 Agent 必须先建立项目边界：本项目只处理 `projects/AI-Parenting-Copilot/` 内的育儿系统，不把工厂根目录 FEOS / Network / TASK_BACKLOG 当作本项目任务来源。

---

## 0. 必读顺序

1. `docs/HANDOFF.md`（本文件）
2. `docs/PROJECT_STATE.md`（当前状态 SSOT）
3. `docs/TASK_BACKLOG.md`（任务状态与验收标准）
4. `docs/ARCHITECTURE_FINAL.md`（唯一架构基线）
5. `docs/ENGINEERING_DESIGN.md`（工程实现蓝图）
6. 工厂根目录 `../../../PROJECT_DOSSIER_V5.md`（工厂能力背景）
7. `docs/DEV_LOG.md` 最新一轮
8. `docs/CHANGELOG.md` 最新一轮
9. `docs/ADR/` 决策记录

不要使用项目内旧拷贝 `docs/PROJECT_DOSSIER_V5.md` 作为执行依据。

---

## 1. 项目定位

AI Parenting Copilot 是家庭私有化 AI 育儿副驾驶系统，目标是在家庭局域网内通过 Mac M1 Max 家庭服务端与 Android App，实现低摩擦记录、离线同步、派生状态、规则安全、告警必达与克制 AI Copilot。

项目根目录：

```text
projects/AI-Parenting-Copilot/
```

---

## 2. 当前真实状态

截至 2026-07-08：

- `APC-T001` 已完成：项目骨架、基础配置、项目级维护文档与 ADR 已创建。
- `APC-T002` 已完成：FastAPI 应用壳、Settings、DI 与公共基础类型已实现。
- `APC-T005` 已完成：结构化日志、Prometheus metrics、OpenTelemetry 基础 tracing、请求日志 middleware 与健康端点已实现。
- `APC-T003` 代码/配置已完成但 BLOCKED：当前沙盒无 Docker CLI，尚未完成容器健康验收。
- `APC-T024` 已完成：Model Gateway Smart Proxy 客户端、routing loader、FakeModelClient。
- `APC-T025` 已完成：Privacy Gateway 适配、PII/canary/media 出站安全测试。
- `APC-T004` 代码已完成但 BLOCKED：metadata/migration/offline SQL 通过，等待 PostgreSQL 空库迁移验收。
- `APC-T006` 代码已完成但 BLOCKED：audit service/decorator/unit tests 通过，等待 audit_log DB immutability 集成验收。
- `APC-T007` 代码已完成但 BLOCKED：Auth/RBAC/JWT/in-memory repo/unit tests 通过，等待 DB repository 与真实 audit 集成验收。
- `APC-T008` dev 代码已完成但 BLOCKED：Auth API 与 in-memory seed 脚本通过，等待 DB 持久化验收。
- `APC-T009` 代码已完成但 BLOCKED：ObservationEvent 契约/idempotency/in-memory repo tests 通过，等待 DB repository 集成验收。
- `APC-T010` dev 代码已完成但 BLOCKED：Events API dev/in-memory flow 通过，等待真实 DB/audit_log 集成验收。
- `APC-T018` 纯逻辑已完成但 BLOCKED：Rule Engine kernel/loader/registry/rules-validate 通过，等待 EvidencePolicy DB/audit 验收。
- `APC-T020` 纯逻辑已完成但 BLOCKED：Medication rules/golden tests 通过，等待 T018 解除。
- `APC-T021` 纯逻辑已完成但 BLOCKED：Triage/Threshold rules/golden tests 通过，等待 T018/T016 解除。
- `APC-T022` 纯逻辑已完成但 BLOCKED：Vaccine planner/golden tests 通过，等待 T018 与规则审查。
- `APC-T023` 纯逻辑已完成但 BLOCKED：Growth fixture/golden tests 通过，等待 T018 与完整 WHO 表验收。
- `APC-T026` 纯逻辑已完成但 BLOCKED：M1-M5 MemorySnapshot/in-memory store tests 通过，等待 T016 与真实 RAG/DB 适配。
- `APC-T027` 纯逻辑已完成但 BLOCKED：Copilot base/registry/logger tests 通过，等待 T026 解除。
- `APC-T028` dev 链路已完成但 BLOCKED：Orchestrator API logger candidate 通过，等待 T027/T006 解除。
- `APC-T029` 纯逻辑已完成但 BLOCKED：Dose Interceptor 安全测试通过，等待 T028 与真实 audit_log 写入。
- `APC-T030` 纯逻辑已完成但 BLOCKED：P0 Copilot wrappers/tests 通过，等待前置 Rule/Orchestrator/Dose/Memory 与真实 DB/audit 集成。
- `APC-T031` dev 代码已完成但 BLOCKED：Alert repo/API/MemoryAuditSink tests 通过，等待 DB/audit 持久化。
- `APC-T032` fake 通道已完成但 BLOCKED：NotificationChannel/FakeFCM/Mac/App/Camera tests 通过，等待真实设备/FCM/TTS。
- `APC-T033` 纯逻辑已完成但 BLOCKED：Notification fan-out/delivery receipts tests 通过，等待 DB delivery repo 与升级状态机。
- Android / firmware 仍为目录占位。

---

## 3. 当前下一步

Task ID：`APC-T003`

任务名称：完成本地基础设施 Docker Compose 与 Alembic 验收

执行前必须再次确认：

- 不改变架构边界。
- 不自研同步，PowerSync 使用官方镜像。
- PostgreSQL 15+、Mosquitto 2.x、PowerSync 仅作为本地开发基础设施。
- SQLAlchemy 2.0 async + asyncpg；迁移使用 Alembic。
- 当前沙盒无 Docker CLI，容器健康验收需在用户 Mac 或可用 Docker 环境完成；未满足 DoD 前不得标记 `APC-T003 DONE`。

---

## 4. 常用命令

在项目根目录运行：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
```

`make run-dev` 已接入 `python3 -m uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8000`。

---

## 5. 文档 SSOT

- 当前状态：`docs/PROJECT_STATE.md`
- 任务状态：`docs/TASK_BACKLOG.md`
- 架构基线：`docs/ARCHITECTURE_FINAL.md`
- 工程设计：`docs/ENGINEERING_DESIGN.md`
- 开发流水：`docs/DEV_LOG.md`
- 变更记录：`docs/CHANGELOG.md`
- 工厂能力背景：工厂根目录 `../../../PROJECT_DOSSIER_V5.md`

冲突优先级：用户当前最新指令 → 本项目 `docs/HANDOFF.md` → `docs/ARCHITECTURE_FINAL.md` → `docs/ENGINEERING_DESIGN.md` → `docs/TASK_BACKLOG.md` → 工厂根目录 `PROJECT_DOSSIER_V5.md` → 源码历史实现。

---

## 6. 架构保护速查

禁止未经用户明确批准：

- 修改架构决策、技术路线、系统边界、模块职责、调用链、核心设计原则。
- 引入新的基础设施或框架。
- 替换已有核心组件。
- 擅自大规模重构。

必须遵守：

1. LLM 只走 Model Gateway。
2. 云端出站只走 Privacy Gateway。
3. 剂量 / 阈值 / 医疗判断只由 Rule Engine 产出。
4. 告警只走 Notification Orchestrator。
5. 所有 mutating 操作必须审计。
6. Android 离线记录不得丢失。

---

## 7. LLM 文件头规则

LLM 新建或修改 Markdown、Python、YAML、Shell 等文件时，必须在文件头记录：

```text
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：YYYY-MM-DD HH:MM:SS
```

JSON 文件不能写注释时，使用 `_forge_trace` 字段。
