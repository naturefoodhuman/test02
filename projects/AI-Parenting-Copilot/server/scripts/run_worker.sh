# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
make ensure-dev-deps
echo "Worker placeholder: FastAPI lifespan workers run in-process for current MVP."
