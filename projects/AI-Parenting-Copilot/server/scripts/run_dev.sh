# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
make ensure-dev-deps
make db-migrate
exec python3 -m uvicorn server.app.main:app --reload --host 127.0.0.1 --port 8000
