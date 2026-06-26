#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

set -euo pipefail

echo "# FORGE local model / gateway status"
echo

check_port() {
  local port="$1"
  local name="$2"
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "✅ $name port $port LISTEN"
    lsof -nP -iTCP:"$port" -sTCP:LISTEN | awk 'NR>1 {print "   PID=" $2 " CMD=" $1}' | sort -u
  else
    echo "⚪ $name port $port not listening"
  fi
}

check_port 4000 "Claude Code Smart Proxy"
check_port 4001 "LiteLLM core gateway"
check_port 8080 "MTPLX Qwen main"
check_port 8082 "MTPLX Gemma reviewer"
check_port 8084 "Qwopus llama.cpp"
check_port 11434 "Ollama"

echo

echo "# AI-related processes"
ps aux | grep -E 'mtplx|llama-server|ollama|smart_proxy|litellm' | grep -v grep || true

echo

echo "# Recent smart proxy log"
tail -30 /tmp/forge_smart_proxy.log 2>/dev/null || echo "No /tmp/forge_smart_proxy.log yet"
