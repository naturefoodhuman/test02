<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# ADR-001 — 项目骨架与工程元数据初始化

| 字段 | 值 |
|---|---|
| 编号 | ADR-001 |
| 状态 | Accepted |
| 日期 | 2026-08-02 |
| 对应任务 | APC-T001 |
| 决策者 | FORGE Factory Orchestrator |

## 1. 背景

AI Parenting Copilot 在 `projects/AI-Parenting/` 从零重建。需要确立项目骨架、工程元数据与文档占位，使后续 APC-T002 ~ APC-T059 可直接在此基础上开发，且任何新 Agent 能在 5–10 分钟内建立心智。

仓库中存在另一个同名项目 `projects/AI-Parenting-Copilot/`（已实现到 APC-T058），与本目录**完全隔离**：本项目以 `docs/ARCHITECTURE_FINAL.md` + `docs/ENGINEERING_DESIGN.md` + `docs/TASK_BACKLOG.md` 为唯一依据从零实现，不参考 Copilot 目录。

## 2. 决策

### 2.1 目录结构

采用 `ENGINEERING_DESIGN.md §3` 推荐结构：

- `server/app/` 下按领域分模块（auth / events / state_engine / rule_engine / notification / camera / mmwave / media / memory / model_gateway / privacy / orchestrator / copilots / observability / health / scheduler / backup / export / normalization / common / gateway），每个领域预留 `domain/` `service/` `infra/` `api/` `tests/` 子结构（按需在后续任务落地）。
- `server/migrations/` Alembic，`server/scripts/` 运维脚本，`server/tests/` 测试（unit/integration/golden/security/e2e）。
- `android/` React Native Android-only，`firmware/esp32c6/` PlatformIO。
- `config/` 规则与设备配置，`deploy/` docker-compose 与 launchd。
- `runtime/` 本地运行时产物（gitignored），`tests/` 跨端 fixtures/e2e/shadow/soak。
- `docs/` 架构 / 工程 / 任务 / 状态 / ADR。

### 2.2 Python 版本与工具链

- 锁定 Python **3.11+**（`pyproject.toml` `requires-python = ">=3.11"`）。
- 包管理用 `uv`（`make install` → `uv sync --extra dev`）。
- Lint/Format：`ruff`（line-length 100，select E/F/W/I/UP/B/SIM/RUF）。
- Typecheck：`mypy`（渐进式，`disallow_untyped_defs=false`，迁移目录与 android/firmware 排除）。
- Test：`pytest` + `pytest-asyncio`（auto mode），markers：slow/integration/golden/security/e2e。

### 2.3 Makefile 目标

至少提供（已实现）：`test` `lint` `typecheck` `docs-check` `governance-check` `run-dev`，外加 `format` `test-all` `test-integration` `security-test` `golden` `rules-validate` `infra-up` `infra-down` `db-migrate` `db-seed` `run-worker` `install`。

### 2.4 .gitignore 铁律

- `runtime/`（媒体 / 日志 / 本地 DB / 密钥 / RAG 索引）整体忽略，仅留 `runtime/.gitkeep` 占位。
- `.env` 与真实密钥（`*.pem` `*.key` `fcm-service-account.json`）忽略，`.env.example` 保留。
- Python 缓存、`.venv`、`.mypy_cache`、`.ruff_cache`、`.pytest_cache` 忽略。
- Android `node_modules` / `build` / `*.apk` / `*.aab` / `*.keystore` 忽略。
- 固件 `.pio` 忽略。
- 媒体文件（`*.mp4` `*.mov` `*.m4a` 等）忽略，但 `tests/fixtures/` 下的测试夹具保留。

### 2.5 文档占位与 SSOT

- `docs/PROJECT_STATE.md`：当前状态 SSOT，含任务状态索引。
- `docs/DEV_LOG.md`：开发日志，每轮记录。
- `docs/CHANGELOG.md`：变更日志。
- `docs/HANDOFF.md`：Agent 接手入口（已存在）。
- `docs/ADR/ADR-001-project-bootstrap.md`：本文件。
- **本项目状态只在 `projects/AI-Parenting/docs/` 下记录，不写入工厂根 docs**，以免影响 `projects/AI-Parenting-Copilot/`。

### 2.6 LLM 文件头留痕

LLM 新建 / 修改的文件头部写明模型名 + 北京时间（精确到秒）。Markdown 用 `<!-- -->` 注释块，Python 用 `#` 注释，JSON 用 `_forge_trace` 字段。人类手写文件不强制。

### 2.7 Factory-first

不复制工厂 `_infra/` 实现，只通过适配层引用（Smart Proxy 4000 / Privacy / Local RAG / Agent / Skill / governance）。本任务只建骨架，适配层在后续任务落地。

## 3. 占位 `__init__.py`

为使 `server` 成为可被 ruff/mypy/pytest 识别的 Python 包，在 `server/`、`server/app/` 及其各领域子包、`server/migrations/`、`server/migrations/versions/`、`server/scripts/`、`server/tests/` 及各测试子目录创建空 `__init__.py`（仅含文件头注释，无业务代码）。业务实现由 APC-T002 起逐任务填充。

## 4. 验证

- `make lint` 不因空项目失败（ruff 对空 `__init__.py` 不报错）。
- `make docs-check` 可运行（占位提示 + PROJECT_STATE 任务索引 grep）。

## 5. 后果

- ✅ 后续任务可直接在骨架上开发，无需重复搭目录。
- ✅ 新 Agent 通过 `README.md` + `docs/HANDOFF.md` 理解入口。
- ✅ `.env.example` 不含真实密钥，`runtime/` 与媒体不入库，隐私边界从骨架起即落实。
- ⚠️ 占位 `__init__.py` 与文档为空壳，真实能力从 APC-T002 起逐步落地；本任务不实现任何业务逻辑。

## 6. 不做

- 不实现 FastAPI 应用、Settings、DB、Schema、审计等（APC-T002 ~ APC-T006）。
- 不接入工厂治理脚本（`docs-check` / `governance-check` 暂为占位，待治理脚本接入后替换）。
- 不修改 `docs/SPEC.md` 或其他 ADR（arch-advisor 职责）。
