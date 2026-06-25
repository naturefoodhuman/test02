#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

echo "[governance] running docs-check (no-write strict mode)..."
python3 scripts/governance_check.py --strict --no-write

echo "[governance] checking whitespace..."
git diff --check

echo "[governance] pre-commit governance checks passed."
