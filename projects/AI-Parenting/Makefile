# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-02 00:00:00

# AI Parenting Copilot — Makefile
# 依据 ENGINEERING_DESIGN.md §12.3 CI 顺序与 §14 Bootstrap 约束。

PYTHON ?= python3
VENV ?= .venv
PKG := server

.DEFAULT_GOAL := help

.PHONY: help
help: ## 显示可用目标
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------------- 质量门 ----------------
.PHONY: lint
lint: ## Ruff 静态检查 + 格式校验
	$(VENV)/bin/ruff check $(PKG) tests
	$(VENV)/bin/ruff format --check $(PKG) tests

.PHONY: format
format: ## Ruff 自动格式化
	$(VENV)/bin/ruff format $(PKG) tests
	$(VENV)/bin/ruff check --fix $(PKG) tests

.PHONY: typecheck
typecheck: ## Mypy 类型检查
	$(VENV)/bin/mypy $(PKG)

.PHONY: test
test: ## 单元测试（排除 slow/integration，CI 默认）
	$(VENV)/bin/pytest -m "not slow and not integration"

.PHONY: test-all
test-all: ## 全量测试（含 integration，需 DB 环境）
	$(VENV)/bin/pytest

.PHONY: test-integration
test-integration: ## 集成测试（需 PARENTING_DATABASE__URL）
	$(VENV)/bin/pytest -m "integration"

.PHONY: security-test
security-test: ## 安全回归套件（Dose/PII/Canary/审计不可删除）
	$(VENV)/bin/pytest tests/security server/tests/security -m "security or not slow"

.PHONY: golden
golden: ## 规则黄金用例
	$(VENV)/bin/pytest tests/golden server/tests/golden -m "golden or not slow"

# ---------------- 规则治理 ----------------
.PHONY: rules-validate
rules-validate: ## 校验 config/rules/** 规则包（Pydantic + hash）
	$(VENV)/bin/python -m server.app.rule_engine.loader --validate config/rules

# ---------------- 文档治理 ----------------
.PHONY: docs-check
docs-check: ## 文档一致性检查（占位：项目级治理脚本接入前给出明确提示）
	@echo "ℹ️ docs-check: 项目级治理脚本尚未接入；请人工核对 docs/PROJECT_STATE.md 与 TASK_BACKLOG.md 状态一致。"
	@bash -c 'grep -q "APC-T" docs/PROJECT_STATE.md 2>/dev/null || echo "⚠️ docs/PROJECT_STATE.md 未包含任务状态索引"'

.PHONY: governance-check
governance-check: ## 治理检查（占位）
	@echo "ℹ️ governance-check: 项目级治理脚本尚未接入；LLM 文件头留痕与 SSOT 一致性请人工复核。"

# ---------------- 基础设施 ----------------
.PHONY: infra-up
infra-up: ## 启动本地基础设施（postgres/mosquitto/powersync）
	cd deploy && docker compose up -d

.PHONY: infra-down
infra-down: ## 停止本地基础设施
	cd deploy && docker compose down

.PHONY: db-migrate
db-migrate: ## Alembic 升级到 head
	$(VENV)/bin/alembic upgrade head

.PHONY: db-seed
db-seed: ## 初始化默认家庭/父母/宝宝档案
	$(VENV)/bin/python server/scripts/seed_family.py

# ---------------- 运行 ----------------
.PHONY: run-dev
run-dev: ## 启动开发服务器（FastAPI + 内嵌 worker）
	$(VENV)/bin/uvicorn server.app.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: run-worker
run-worker: ## 启动常驻 worker（MQTT/Camera/Scheduler/Normalization/Notification 升级）
	$(VENV)/bin/python server/scripts/run_worker.sh

# ---------------- 安装 ----------------
.PHONY: install
install: ## 安装项目与开发依赖（uv）
	uv sync --extra dev
