#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 12:10:00
set -euo pipefail
cd "$(dirname "$0")/.."
export NIM_PROXY_HOST="${NIM_PROXY_HOST:-127.0.0.1}"
export NIM_PROXY_PORT="${NIM_PROXY_PORT:-4010}"
python3 _infra/nim_proxy.py
