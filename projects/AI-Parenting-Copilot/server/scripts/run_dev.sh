#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:48:00

set -euo pipefail

cd "$(dirname "$0")/../.."

if [[ -z "${PARENTING_DATABASE__URL:-}" ]]; then
  echo "[run-api] PARENTING_DATABASE__URL is not set; API will start in dev-mock DB mode." >&2
else
  echo "[run-api] Using PARENTING_DATABASE__URL=${PARENTING_DATABASE__URL}" >&2
fi
if [[ -n "${PARENTING_POWERSYNC__URL:-}" ]]; then
  echo "[run-api] Using PARENTING_POWERSYNC__URL=${PARENTING_POWERSYNC__URL}" >&2
fi

echo "[run-api] Starting FastAPI at http://127.0.0.1:8000" >&2
echo "[run-api] In another terminal run: make api-health-smoke" >&2

make ensure-dev-deps
if [[ -n "${PARENTING_DATABASE__URL:-}" ]]; then
  make db-migrate
fi
exec python3 -m uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8000
