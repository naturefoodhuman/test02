#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 12:55:00
set -euo pipefail
cd "$(dirname "$0")/.."

load_env_file() {
  local env_file="$1"
  if [ ! -f "$env_file" ]; then
    return 0
  fi
  while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    raw_line=$(printf '%s' "$raw_line" | tr -d '
')
    case "$raw_line" in
      ''|'#'*) continue ;;
    esac
    if [[ "$raw_line" != *=* ]]; then
      continue
    fi
    local key="${raw_line%%=*}"
    local value="${raw_line#*=}"
    key=$(printf '%s' "$key" | sed -e 's/^export //' -e 's/[[:space:]]//g')
    value=$(printf '%s' "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    value=$(printf '%s' "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    if [ -n "$key" ] && [ -z "${!key:-}" ]; then
      export "$key=$value"
    fi
  done < "$env_file"
}

load_env_file ".env"

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
