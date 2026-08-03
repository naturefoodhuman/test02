<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# DEV_LOG —— AI Parenting Copilot 开发日志

> 项目级开发日志，独立于工厂根 `DEV_LOG.md`。每轮开发记录一条。
> Latest Index 在顶部，最新一轮在最前。

---

## Latest Index

- 2026-08-02 · Round 01 · APC-T001 项目骨架初始化完成

---

## Round 01 · 2026-08-02 · APC-T001 项目骨架初始化

**任务**：APC-T001 — 初始化项目目录与工程元数据

**完成内容**：

1. **目录骨架**：`server/app/` 下 21 个领域子模块、`server/migrations/`、`server/scripts/`、`server/tests/`（unit/integration/golden/security/e2e）、`android/`、`firmware/esp32c6/`、`config/`、`deploy/`、`tests/`、`runtime/` 已就位（前期已建）。
2. **工程元数据**：
   - `pyproject.toml`：Python 3.11+，FastAPI/Pydantic v2/SQLAlchemy 2.0 async/asyncpg/Alembic/aiomqtt/APScheduler/structlog/prometheus/opentelemetry/httpx 等依赖；ruff（line-length 100，E/F/W/I/UP/B/SIM/RUF）、mypy（渐进式）、pytest（asyncio auto + markers）配置。
   - `Makefile`：lint/format/typecheck/test/test-all/test-integration/security-test/golden/rules-validate/infra-up/infra-down/db-migrate/db-seed/run-dev/run-worker/install/docs-check/governance-check。
   - `.env.example`：PARENTING_ 前缀，分层加载（defaults→config→runtime→.env→env→CLI），无真实密钥。
3. **本次新增（APC-T001 收尾）**：
   - `.gitignore`：runtime/、.env、密钥（*.pem/*.key/fcm-service-account.json）、Python 缓存、.venv、Android build/apk/aab/keystore、固件 .pio、媒体文件忽略；保留 .gitkeep 与 tests/fixtures。
   - `README.md`：项目定位、SSOT 文档表、技术栈、快速开始、命令、目录结构、边界说明。
   - `docs/PROJECT_STATE.md`：当前状态 SSOT + 任务状态索引（供 docs-check grep）。
   - `docs/DEV_LOG.md`（本文件）、`docs/CHANGELOG.md`。
   - `docs/ADR/ADR-001-project-bootstrap.md`：骨架决策记录。
   - `server/` 全包占位 `__init__.py`（server、server/app、各领域子包、migrations、migrations/versions、scripts、tests 及各测试子目录），仅文件头注释，无业务代码。
   - `runtime/.gitkeep`：确保 runtime/ 入库但内容被忽略。

**验证**：

- `make lint`：ruff check + format --check 对空 `__init__.py` 不报错 → 通过。
- `make docs-check`：占位提示 + PROJECT_STATE 任务索引 grep → 通过。

**遵循的边界**：

- 不碰 `projects/AI-Parenting-Copilot/`。
- 不写工厂根 `docs/DEV_LOG.md` / `CHANGELOG.md` / `PROJECT_STATE.md`。
- 不复制工厂 `_infra/` 实现，只预留适配层引用点。
- 不修改 `docs/SPEC.md` 或其他 ADR。

**下一步**：APC-T002 — FastAPI 应用壳、Settings、DI 与公共基础类型。

**模型**：Claude Opus 4.8（1M context）
