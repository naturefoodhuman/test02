#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:20:00

# FORGE Network health check (E10-C1-S1-T1)
#
# Usage:
#   scripts/health-check.sh
#   scripts/health-check.sh --static   # config-only validation, no external services

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

STATIC_ONLY=0
if [[ "${1:-}" == "--static" ]]; then
  STATIC_ONLY=1
elif [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '1,16p' "$0"
  exit 0
elif [[ -n "${1:-}" ]]; then
  echo "ERROR: unknown argument: $1" >&2
  exit 2
fi

if [[ -n "${FORGE_ROOT:-}" ]]; then
  ROOT="$FORGE_ROOT"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
cd "$ROOT"

FAILURES=0
WARNINGS=0

ok() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; WARNINGS=$((WARNINGS + 1)); }
fail() { echo -e "${RED}❌ $1${NC}"; FAILURES=$((FAILURES + 1)); }

py_config() {
  python - <<'PY'
from _infra.network.config_loader import load_network_config
cfg = load_network_config()
print(cfg.search.searxng.base_url)
print(cfg.extract.crawl4ai.base_url)
print(cfg.privacy_gateway.qwen_model)
print(cfg.local_rag.embed_model)
print(cfg.mcp_guard.audit_db)
print(cfg.local_rag.rag_db)
PY
}

check_config() {
  if mapfile -t CFG < <(py_config); then
    SEARXNG_URL="${CFG[0]}"
    CRAWL4AI_URL="${CFG[1]}"
    QWEN_MODEL="${CFG[2]}"
    BGE_MODEL="${CFG[3]}"
    AUDIT_DB="${CFG[4]}"
    RAG_DB="${CFG[5]}"
    ok "network config loads"
  else
    fail "network config failed to load"
    SEARXNG_URL="http://127.0.0.1:8080"
    CRAWL4AI_URL="http://127.0.0.1:11235"
    QWEN_MODEL="qwen3:8b"
    BGE_MODEL="bge-m3"
    AUDIT_DB="runtime/audit.db"
    RAG_DB="runtime/rag.db"
  fi
}

check_url() {
  local name="$1"
  local url="$2"
  local timeout="${3:-5}"
  if command -v curl >/dev/null 2>&1 && curl -fsS --max-time "$timeout" "$url" >/dev/null; then
    ok "$name reachable: $url"
  else
    fail "$name unreachable: $url"
  fi
}

check_command() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    ok "$name ok"
  else
    fail "$name failed: $*"
  fi
}

check_ollama_model() {
  local model="$1"
  if ! command -v ollama >/dev/null 2>&1; then
    fail "ollama command not found"
    return
  fi
  if ollama list 2>/dev/null | awk '{print $1}' | grep -Fxq "$model"; then
    ok "ollama model present: $model"
  else
    fail "ollama model missing: $model"
  fi
}

check_sqlite_db() {
  local name="$1"
  local path="$2"
  if [[ ! -f "$path" ]]; then
    fail "$name missing: $path"
    return
  fi
  if python - "$path" <<'PY'
import sqlite3, sys
path = sys.argv[1]
with sqlite3.connect(path) as conn:
    conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
PY
  then
    ok "$name readable: $path"
  else
    fail "$name unreadable: $path"
  fi
}

check_static_files() {
  local files=(
    "config/network.yaml"
    "config/mcp_lockfile.yaml"
    "config/mode_policies.yaml"
    "docker/docker-compose.yml"
    "docker/searxng/settings.yml"
    ".mcp.json.coding"
    ".mcp.json.research"
    ".mcp.json.private"
  )
  for f in "${files[@]}"; do
    if [[ -f "$f" ]]; then ok "static file exists: $f"; else fail "static file missing: $f"; fi
  done
}

check_config
check_static_files

if [[ "$STATIC_ONLY" == "1" ]]; then
  echo "Static health check complete: failures=$FAILURES warnings=$WARNINGS"
  exit $([[ "$FAILURES" == "0" ]] && echo 0 || echo 1)
fi

check_url "SearXNG" "${SEARXNG_URL%/}/search?q=test&format=json" 5
check_url "Crawl4AI" "${CRAWL4AI_URL%/}/health" 5
check_command "ollama ps" ollama ps
check_ollama_model "$QWEN_MODEL"
check_ollama_model "$BGE_MODEL"
check_sqlite_db "Audit DB" "$AUDIT_DB"
check_sqlite_db "RAG DB" "$RAG_DB"

echo "Health check complete: failures=$FAILURES warnings=$WARNINGS"
exit $([[ "$FAILURES" == "0" ]] && echo 0 || echo 1)
