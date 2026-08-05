#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 12:55:00
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

export NIM_PROXY_HOST="${NIM_PROXY_HOST:-127.0.0.1}"
export NIM_PROXY_PORT="${NIM_PROXY_PORT:-4010}"

key_count=0
for i in {1..10}; do
  var="NVIDIA_API_KEY_${i}"
  if [ -n "${!var:-}" ]; then
    key_count=$((key_count + 1))
  fi
done

if [ "$key_count" -eq 0 ]; then
  echo "ERROR: No NVIDIA NIM keys configured. Set NVIDIA_API_KEY_1, NVIDIA_API_KEY_2, ..." >&2
  exit 1
fi

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

exec python3 _infra/nim_proxy.py
