<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# HANDOFF —— AI Parenting Copilot Agent 接手入口

> 目标：任何新 Agent 在 5–10 分钟内建立当前项目心智，并能安全继续开发。
> 本文件是项目级交接文档，独立于工厂根 `HANDOFF.md`。本项目状态只在此处与
> `docs/PROJECT_STATE.md` / `docs/DEV_LOG.md` / `docs/CHANGELOG.md` 记录，
> **不写入工厂根的 DEV_LOG/CHANGELOG/PROJECT_STATE**，以免影响同仓库的
> `projects/AI-Parenting-Copilot/` 项目。

---

## 0. 必读顺序

1. `docs/HANDOFF.md`（本文件）
2. `docs/PROJECT_STATE.md`（当前状态 SSOT）
3. `docs/TASK_BACKLOG.md`（任务状态 SSOT）
4. `docs/ARCHITECTURE_FINAL.md`（唯一架构基线）
5. `docs/ENGINEERING_DESIGN.md`（工程实现蓝图）
6. `docs/DEV_LOG.md` 顶部 Latest Index + 最新一轮
7. `docs/CHANGELOG.md` 顶部 Latest Index + 最新一轮
8. `docs/ADR/ADR-001-project-bootstrap.md`

冲突时优先级（用户指令铁律）：
> P0 用户最新指令 → P1 HANDOFF.md → P2 ARCHITECTURE_FINAL.md
> → P3 ENGINEERING_DESIGN.md → P4 TASK_BACKLOG.md → P5 PROJECT_DOSSIER_V5.md → P6 源码历史

---

## 0.5 工作纪律铁律（用户 2026-08-12 授权，后续会话必须遵守）

本项目开发采用**高度自主**模式，Agent 不得在任务中途停下来请示用户，除非满足下列停止条件之一：

### 自主推进范围（一律自行处理，不请示）

- 按 TASK_BACKLOG §4 MVP 路径顺序推进任务，逐个做到 DoD 满足。
- 实现、测试、静态检查（ruff/mypy）、文档同步（PROJECT_STATE/DEV_LOG/CHANGELOG）。
- 修复测试失败、lint/typecheck 错误、代码与文档脱节。
- **Git 提交**：开发过程中有必要时**直接提交，不必向用户请示**。遵循 §3 Git 纪律（先 `git status`/`git fetch`、不覆盖用户提交、不 force push main、不提交 secrets/.env）。
- 跨任务的小幅重构、命名对齐、依赖更新（无架构边界变更）。

### 仅在以下情况停止并向用户汇报/请示

1. **上下文接近 900K tokens**：强制触发——先更新所有维护文档（PROJECT_STATE/DEV_LOG/CHANGELOG/TASK_BACKLOG 状态）形成完整外部记忆快照，**再**暂停开发并向用户汇报当前进度与下一步。不要在 900K 之前因"任务做完一个"就停。
2. **重大决策需用户裁决**：例如架构边界变更（需 ADR 但用户未授权）、引入新基础设施/新依赖、与 `AI-Parenting-Copilot/` 的隔离边界冲突、安全/隐私铁律的例外、用户先前指令相互矛盾。这类情况先写清问题与选项再请示，不要自行拍板。
3. **遇到红线阻断**：如 harness 拦截 `.env` 操作、本地环境不可恢复的冲突、需要用户机器上的凭据/权限——已尝试合理绕过仍无法推进时，汇报阻塞点。

### 禁止行为

- **禁止**做完一个任务就停下问"是否继续/是否提交"——这违背自主推进授权。
- **禁止**在未触达停止条件时提前汇报"本轮完成"并等待——应继续下一个任务。
- **禁止**用请示掩盖本可自行决策的犹豫——能查文档/代码确认的不确定，先查再动手。

### 提交节奏建议

- 每个任务达到 DoD（功能+测试+静态检查+文档）后提交一次，commit message 遵循项目风格（`feat(t0xx):` / `fix(t0xx):` / `docs:` 等）。
- 文档补齐/静态检查修复可单独提交，或与对应代码改动合并提交。
- 提交前 `git status --short --branch` + `git fetch origin main`；本地有领先提交时保留，不 force push。

---

## 1. 项目定位与关键边界

- **项目实体**：`projects/AI-Parenting/`（本目录），从零重建。
- **架构事实来源**：`docs/ARCHITECTURE_FINAL.md`（唯一）。
- **工程实现依据**：`docs/ENGINEERING_DESIGN.md`。
- **任务清单**：`docs/TASK_BACKLOG.md`（APC-T001 ~ APC-T059）。
- **工厂能力来源**：仓库根 `PROJECT_DOSSIER_V5.md` + `_infra/`、`config/`。

### ⚠️ 不可触碰的边界

仓库中存在另一个同名项目 `projects/AI-Parenting-Copilot/`，它已实现到 APC-T058
（76 个测试，171 passed）。**该目录与本目录完全隔离**：

- **不读** `AI-Parenting-Copilot/` 的任何源码、进度、文档作为本项目的实现依据。
- **不动** `AI-Parenting-Copilot/` 的任何文件。
- **不写入**工厂根 `docs/DEV_LOG.md` / `docs/CHANGELOG.md` / `docs/PROJECT_STATE.md`
  关于本项目的记录，只在 `projects/AI-Parenting/docs/` 下记录。

本项目以 `docs/ARCHITECTURE_FINAL.md` + `docs/ENGINEERING_DESIGN.md` +
`docs/TASK_BACKLOG.md` 为唯一依据从零实现，不参考 Copilot 目录的实现。

---

## 2. 当前真实状态（2026-08-12）

### 已完成
- 项目目录骨架（`server/app/` 下全部子模块、`android/`、`firmware/esp32c6/`、
  `config/`、`deploy/`、`tests/`、`runtime/`）。
- `pyproject.toml`（依赖 + ruff + mypy + pytest 配置，Python 3.11+）。
- `Makefile`（test/lint/typecheck/docs-check/governance-check/run-dev/infra-up/db-migrate）。
- `.env.example`（PARENTING_ 前缀，分层加载）。
- `docs/HANDOFF.md`、`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/ADR/`。
- **Milestone 1（APC-T001 ~ APC-T006）全部 DONE**：骨架、FastAPI 壳、Docker Compose + Alembic、28 表核心 Schema、结构化日志/metrics/tracing/health、审计服务 + @audit 装饰器。
- **Milestone 2 进行中**：
  - APC-T007 ~ APC-T011 **DONE**：Auth/RBAC Domain + JWT（HS256 标准库）、Auth API + 设备注册 + seed_family、ObservationEvent Domain + 幂等 upsert、Events API（create/list/correct/soft-delete）、PG LISTEN/NOTIFY 事件总线 + EventWorker 崩溃恢复。
  - 全量 230 passed（191 unit + 39 integration），ruff/mypy 干净。
  - 2026-08-12 修复 T007 遗留的 `JwtService.parse` 时钟不对称 bug（parse 持有注入 Clock，与 issue 对称）。

### 进行中
- **APC-T012 PowerSync 适配、同步契约校验与冲突软提示基础**（半成品）：
  - 已写：`server/app/sync/service/contract_validator.py`（同步契约校验）、`conflict_detector.py`（5 分钟内重复 feeding 软提示）。
  - 缺口：无测试、未接入 DI/main、`sync-rules.yaml` 仍占位、未文档化。2026-08-12 修复 contract_validator mypy 错误。
  - 待补齐才算 DONE：测试 + DI 装配 + sync-rules.yaml + 文档。

### 未开始
- APC-T013 ~ APC-T059（后续里程碑，见 TASK_BACKLOG）。

---

## 3. 任务依赖图（地基阶段）

```
APC-T001 (骨架)
  ├─ APC-T002 (FastAPI 壳)
  │    ├─ APC-T003 (Docker+Alembic)
  │    │    └─ APC-T004 (核心 Schema)
  │    │         └─ APC-T006 (审计)
  │    └─ APC-T005 (可观测性)
  │         └─ APC-T006 (审计)
  └─ APC-T003
```

MVP 路径（TASK_BACKLOG §4）：T001 → T002 → T003 → T004 → T005 → T006 →
T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 →
T045 → T046 → T047 → T048 → T049 → T055 → T056。

---

## 4. 架构铁律速查（开发须遵守）

1. **本地优先**：主控与权威数据在家庭局域网内 Mac；离线可完整记录，不丢记录。
2. **Rule/LLM 分离**：剂量/阈值/医疗判定唯一由 Rule Engine 产出；LLM 不得自由
   计算剂量，输出经 Dose Interceptor 拦截 mg/ml/滴。
3. **隐私边界**：视频/图片/音频/医疗记录不出局域网；云端 LLM 仅收经 Privacy
   Gateway 脱敏后的文本。
4. **告警必达**：红/橙告警多通道送达 + Mac/摄像头扬声器本地兜底；红色未送达目标为 0。
5. **可审计**：所有 mutating 操作写不可删除审计日志（REVOKE UPDATE/DELETE）。
6. **Factory-first**：模型路由（Smart Proxy 4000）、Privacy、Local RAG、Agent/Skill、
   治理一律复用工厂 `_infra/`，通过适配层引用，不复制实现。
7. **单一入口**：LLM 只走 Model Gateway；剂量只走 Rule Engine；告警只走
   Notification Orchestrator；云端出站只走 Privacy Gateway。
8. **边界变更须 ADR**：任何模块职责或架构边界调整前先写 ADR，不自行合并。

---

## 5. 技术栈（ENGINEERING_DESIGN §1.2，社区成熟选型）

- 服务端：Python 3.11+ / FastAPI + Uvicorn / Pydantic v2 / SQLAlchemy 2.0 async +
  asyncpg / Alembic / PostgreSQL 15+ / PowerSync / Mosquitto / aiomqtt /
  APScheduler / structlog / prometheus_client / OpenTelemetry / tenacity / cachetools。
- 安卓：React Native Android-only + op-sqlite + @powersync/react-native +
  @react-native-firebase/messaging + @notifee/react-native + WorkManager。
- 固件：ESP32C6 + PlatformIO + PubSubClient。
- 测试：pytest + pytest-asyncio + hypothesis + testcontainers + freezegun + ruff + mypy。

---

## 6. 常用命令

```bash
cd projects/AI-Parenting

# 质量
make lint          # ruff check + format --check
make typecheck     # mypy
make test          # 单元测试（排除 slow/integration）

# 基础设施
make infra-up      # docker compose up -d（postgres/mosquitto/powersync）
make db-migrate    # alembic upgrade head
make db-seed       # seed_family.py

# 运行
make run-dev       # uvicorn server.app.main:app --reload

# 文档治理
make docs-check
make governance-check
```

---

## 7. LLM 文件头留痕规则

LLM 新建/修改的文件必须更新文件头：

```text
# 创建/修改该文件的LLM大模型：<实际模型名>
# 创建时间（北京时间）：<YYYY-MM-DD HH:MM:SS>
```

Markdown 用 `<!-- -->` 注释块。JSON 用 `_forge_trace` 字段。人类手写文件不强制。

---

## 8. 接手第一步

1. 读本文件（含 **§0.5 工作纪律铁律**）+ `docs/PROJECT_STATE.md` + `docs/TASK_BACKLOG.md`。
2. 查 TaskList 确认当前 in_progress 任务（当前为 **APC-T012**，半成品，缺口见 PROJECT_STATE §3）。
3. 按 TASK_BACKLOG §4 MVP 路径顺序**自主推进**（见 §0.5，勿中途请示），每完成一个任务：
   - 更新 `docs/PROJECT_STATE.md` 与 `docs/TASK_BACKLOG.md` 状态。
   - 在 `docs/DEV_LOG.md` 记一轮，`docs/CHANGELOG.md` 记变更。
   - 满足 DoD（功能+测试+静态检查+文档+验收标准）后才标 DONE。
   - **直接提交**（§0.5 授权，不必请示）。
4. **不碰** `projects/AI-Parenting-Copilot/`，**不写**工厂根 docs。
5. **外部记忆纪律**：代码落地后必须同步 PROJECT_STATE/DEV_LOG/CHANGELOG，避免"代码已提交但文档脱节"（T010/T011 曾出现此情况，2026-08-12 已补齐）。
6. **停止条件**：仅当上下文接近 900K、遇重大决策需裁决、或红线阻断时才暂停汇报（详见 §0.5）。
