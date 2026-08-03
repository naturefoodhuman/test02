<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# CHANGELOG —— AI Parenting Copilot 变更日志

> 项目级变更日志，独立于工厂根 `CHANGELOG.md`。
> 格式参考 Keep a Changelog；版本号对应里程碑 / 任务批次。
> Latest Index 在顶部，最新版本在最前。

---

## Latest Index

- [0.1.0] - 2026-08-02 - APC-T001 项目骨架初始化

---

## [0.1.0] - 2026-08-02

### Added — APC-T001 项目骨架与工程元数据

- **目录结构**：`server/app/`（21 领域子模块）、`server/migrations/`、`server/scripts/`、`server/tests/`（unit/integration/golden/security/e2e）、`android/`、`firmware/esp32c6/`、`config/`、`deploy/`、`tests/`、`runtime/`。
- **`pyproject.toml`**：Python 3.11+ 依赖与工具链（ruff / mypy / pytest）配置。
- **`Makefile`**：lint / typecheck / test / security-test / golden / rules-validate / infra-up / db-migrate / run-dev / docs-check / governance-check 等目标。
- **`.env.example`**：PARENTING_ 前缀分层加载样例，无真实密钥。
- **`.gitignore`**：runtime/、.env、密钥、媒体、缓存、Android/固件构建产物忽略；保留 .gitkeep 与 fixtures。
- **`README.md`**：项目入口、SSOT 文档表、快速开始、命令、目录结构、边界说明。
- **`docs/PROJECT_STATE.md`**：当前状态 SSOT 与任务状态索引。
- **`docs/DEV_LOG.md`**：开发日志。
- **`docs/CHANGELOG.md`**：本文件。
- **`docs/ADR/ADR-001-project-bootstrap.md`**：骨架决策记录。
- **占位 `__init__.py`**：`server/` 全包（含各领域子包、migrations、scripts、tests 子目录），仅文件头注释，待 APC-T002 起填充。
- **`runtime/.gitkeep`**：确保 runtime/ 入库但内容被忽略。

### 验证

- `make lint` 通过（空 `__init__.py` 不触发 ruff 报错）。
- `make docs-check` 通过（占位提示 + PROJECT_STATE 任务索引 grep）。

### 边界

- 不碰 `projects/AI-Parenting-Copilot/`。
- 不写工厂根 docs。
- 不复制工厂 `_infra/` 实现。
