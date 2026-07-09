# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 22:55:00

PYTHON ?= python3
PROJECT_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
DEPLOY_ENV := $(shell test -f deploy/.env && echo deploy/.env || echo deploy/.env.example)

.PHONY: ensure-dev-deps install-dev test lint typecheck docs-check governance-check rules-validate run-dev infra-up infra-down infra-logs db-migrate db-current backup-dry-run security-test e2e-fake-test clean

ensure-dev-deps:
	@$(PYTHON) server/scripts/ensure_dev_deps.py

install-dev:
	@$(PYTHON) -m pip install -e ".[dev]"

test: ensure-dev-deps
	@if find tests -name 'test_*.py' -print -quit | grep -q .; then \
		$(PYTHON) -m pytest tests -q; \
	else \
		echo "No tests found."; \
	fi

lint: ensure-dev-deps
	@$(PYTHON) -m compileall -q server tests
	@$(PYTHON) -m ruff check server tests

typecheck: ensure-dev-deps
	@$(PYTHON) -m mypy server/app

docs-check:
	@test -f README.md
	@test -f docs/ARCHITECTURE_FINAL.md
	@test -f docs/ENGINEERING_DESIGN.md
	@test -f docs/TASK_BACKLOG.md
	@test -f docs/PROJECT_STATE.md
	@test -f docs/DEV_LOG.md
	@test -f docs/CHANGELOG.md
	@test -f docs/HANDOFF.md
	@test -f docs/ADR/ADR-001-project-bootstrap.md
	@test -f server/app/main.py
	@test -f server/app/settings.py
	@test -f server/app/observability/logger.py
	@test -f deploy/docker-compose.yml
	@test -f deploy/.env.example
	@test -f alembic.ini
	@test -f server/app/db.py
	@test -f server/app/models.py
	@test -f server/migrations/versions/0001_initial_schema.py
	@test -f server/app/observability/audit.py
	@test -f server/app/common/audit_decorator.py
	@test -f server/app/events/domain/observation_event.py
	@test -f server/app/events/infra/repository.py
	@test -f server/app/events/api/routes.py
	@test -f server/app/rule_engine/kernel.py
	@test -f server/app/rule_engine/loader.py
	@test -f server/app/rule_engine/domains/medication.py
	@test -f server/app/rule_engine/domains/vaccine.py
	@test -f server/app/rule_engine/domains/growth.py
	@test -f server/app/memory/injector.py
	@test -f server/app/copilots/logger_copilot.py
	@test -f server/app/copilots/vaccine_planner.py
	@test -f server/app/copilots/growth_milestone.py
	@test -f server/app/copilots/medication_safety.py
	@test -f server/app/orchestrator/dose_interceptor.py
	@test -f server/app/orchestrator/orchestrator.py
	@test -f server/app/notification/alert_repo.py
	@test -f server/app/notification/orchestrator.py
	@test -f server/app/notification/channels/base.py
	@test -f server/app/camera/sleep_session.py
	@test -f server/app/camera/rtsp_client.py
	@test -f config/devices.yaml
	@test -f server/app/mmwave/frame_parser.py
	@test -f server/app/mmwave/sensor_event_mapper.py
	@test -f server/app/media/storage.py
	@test -f server/app/backup/pg_dump_task.py
	@test -f server/scripts/mock_mmwave_publisher.py
	@test -f tests/fakes.py
	@test -f firmware/esp32c6/platformio.ini
	@test -f server/app/export/service.py
	@test -f server/app/camera/fusion.py
	@test -f server/app/camera/vlm_dispatcher.py
	@test -f server/scripts/ensure_dev_deps.py
	@test -f server/migrations/env.py
	@test -f server/app/model_gateway/client.py
	@test -f server/app/privacy/adapter.py
	@test -f config/routing_plans.yaml
	@grep -q "projects/AI-Parenting-Copilot/" docs/ARCHITECTURE_FINAL.md
	@grep -q "projects/AI-Parenting-Copilot/" docs/ENGINEERING_DESIGN.md
	@grep -q "APC-T001" docs/TASK_BACKLOG.md
	@grep -q "APC-T001" docs/DEV_LOG.md
	@grep -q "APC-T002" docs/TASK_BACKLOG.md
	@grep -q "APC-T005" docs/TASK_BACKLOG.md
	@echo "Project docs-check passed."

rules-validate: ensure-dev-deps
	@$(PYTHON) -m server.app.rule_engine.loader config/rules

governance-check: docs-check
	@echo "Project-level governance placeholder passed. Factory governance remains at repository root."

infra-up:
	@docker compose --env-file $(DEPLOY_ENV) -f deploy/docker-compose.yml up -d

infra-down:
	@docker compose --env-file $(DEPLOY_ENV) -f deploy/docker-compose.yml down

infra-logs:
	@docker compose --env-file $(DEPLOY_ENV) -f deploy/docker-compose.yml logs -f

db-migrate: ensure-dev-deps
	@$(PYTHON) -m alembic -c alembic.ini upgrade head

db-current: ensure-dev-deps
	@$(PYTHON) -m alembic -c alembic.ini current

security-test: ensure-dev-deps
	@$(PYTHON) -m pytest tests/security -q

e2e-fake-test: ensure-dev-deps
	@$(PYTHON) -m pytest tests/e2e -q

backup-dry-run: ensure-dev-deps
	@$(PYTHON) -c "from server.app.backup.pg_dump_task import PGDumpTask; from server.app.backup.media_archive import MediaArchiveTask; print(PGDumpTask().plan(database_url='postgresql://parenting:parenting@127.0.0.1:5432/parenting').shell_safe_command); print(MediaArchiveTask().plan().output_path)"
run-dev: ensure-dev-deps
	@$(PYTHON) -m uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8000

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
