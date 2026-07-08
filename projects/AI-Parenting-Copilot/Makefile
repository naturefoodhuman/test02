# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:08:00

PYTHON ?= python3
PROJECT_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

.PHONY: test lint typecheck docs-check governance-check run-dev clean

test:
	@if find tests -name 'test_*.py' -print -quit | grep -q .; then \
		$(PYTHON) -m pytest tests -q; \
	else \
		echo "No tests yet for APC-T001 skeleton."; \
	fi

lint:
	@$(PYTHON) -m compileall -q server tests
	@if $(PYTHON) -m ruff --version >/dev/null 2>&1; then \
		$(PYTHON) -m ruff check server tests; \
	else \
		echo "ruff not installed; compileall fallback passed for APC-T001 skeleton."; \
	fi

typecheck:
	@if $(PYTHON) -m mypy --version >/dev/null 2>&1; then \
		$(PYTHON) -m mypy server/app; \
	else \
		echo "mypy not installed; typecheck skipped until dev dependencies are installed."; \
	fi

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
	@grep -q "projects/AI-Parenting-Copilot/" docs/ARCHITECTURE_FINAL.md
	@grep -q "projects/AI-Parenting-Copilot/" docs/ENGINEERING_DESIGN.md
	@grep -q "APC-T001" docs/TASK_BACKLOG.md
	@grep -q "APC-T001" docs/DEV_LOG.md
	@echo "Project docs-check passed."

governance-check: docs-check
	@echo "Project-level governance placeholder passed. Factory governance remains at repository root."

run-dev:
	@echo "APC-T002 will implement FastAPI app startup. No dev server is available in APC-T001."

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
