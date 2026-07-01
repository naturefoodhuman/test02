#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

set -euo pipefail

MODE="${1:-models}"

echo "# Stopping FORGE local AI processes (mode=$MODE)"

kill_port() {
  local port="$1"
  local pids
  pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "Stopping port $port: $pids"
    kill $pids 2>/dev/null || true
    sleep 1
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo "Force stopping port $port: $pids"
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

# Gateways and local model backends.
kill_port 4000
kill_port 4001
kill_port 8080
kill_port 8082
kill_port 8084

pkill -f 'mtplx.*8080' 2>/dev/null || true
pkill -f 'mtplx.*8082' 2>/dev/null || true
pkill -f 'llama-server.*8084' 2>/dev/null || true
pkill -f 'smart_proxy.py' 2>/dev/null || true
pkill -f 'smart_proxy_streaming.py' 2>/dev/null || true
pkill -f 'litellm.*4001' 2>/dev/null || true

if [ "$MODE" = "--all" ] || [ "$MODE" = "all" ]; then
  echo "Stopping Ollama as well (--all)"
  kill_port 11434
  pkill -f 'ollama' 2>/dev/null || true
fi

echo "✅ Stop command sent. Check with: scripts/model_status.sh"
