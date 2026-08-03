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

## 2. 当前真实状态（2026-08-02）

### 已完成
- 项目目录骨架（`server/app/` 下全部子模块、`android/`、`firmware/esp32c6/`、
  `config/`、`deploy/`、`tests/`、`runtime/`）。
- `pyproject.toml`（依赖 + ruff + mypy + pytest 配置，Python 3.11+）。
- `Makefile`（test/lint/typecheck/docs-check/governance-check/run-dev/infra-up/db-migrate）。
- `.env.example`（PARENTING_ 前缀，分层加载）。
- `docs/HANDOFF.md`（本文件）。

### 进行中
- **APC-T001 初始化项目目录与工程元数据**（TaskList #1，in_progress）。
  - 还差：`.gitignore`、`README.md`、`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、
    `docs/CHANGELOG.md`、`docs/ADR/ADR-001-project-bootstrap.md`、
    `server/app/__init__.py` 等占位 `__init__.py`、`runtime/.gitkeep`。
  - 验证：`make lint` 不因空项目失败；`make docs-check` 可运行。

### 未开始
- APC-T002 ~ APC-T006（地基阶段，TaskList #2~#6，依赖关系已设置）。
- APC-T007 ~ APC-T059（后续里程碑）。

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

1. 读本文件 + `docs/PROJECT_STATE.md` + `docs/TASK_BACKLOG.md`。
2. 查 TaskList 确认当前 in_progress 任务（当前为 APC-T001）。
3. 按 TASK_BACKLOG §4 MVP 路径顺序推进，每完成一个任务：
   - 更新 `docs/PROJECT_STATE.md` 与 `docs/TASK_BACKLOG.md` 状态。
   - 在 `docs/DEV_LOG.md` 记一轮，`docs/CHANGELOG.md` 记变更。
   - 满足 DoD（功能+测试+静态检查+文档+验收标准）后才标 DONE。
4. **不碰** `projects/AI-Parenting-Copilot/`，**不写**工厂根 docs。
