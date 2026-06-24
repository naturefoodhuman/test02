#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 14:54:47

# Switch Claude Code MCP mode by updating .mcp.json symlink.
# Usage:
#   scripts/switch-mode.sh coding|research|private
#   scripts/switch-mode.sh current

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  switch-mode.sh <coding|research|private|current>

Environment:
  FORGE_ROOT  Project root (default: git top-level or current directory)
USAGE
}

MODE="${1:-}"
if [[ -z "$MODE" || "$MODE" == "-h" || "$MODE" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -n "${FORGE_ROOT:-}" ]]; then
  ROOT="$FORGE_ROOT"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

cd "$ROOT"

if [[ "$MODE" == "current" || "$MODE" == "status" ]]; then
  if [[ -L ".mcp.json" ]]; then
    target="$(readlink .mcp.json)"
    echo "current: ${target#.mcp.json.}"
    echo "target: $target"
    exit 0
  fi
  if [[ -e ".mcp.json" ]]; then
    echo "current: custom-file"
    echo "target: .mcp.json"
    exit 0
  fi
  echo "current: none"
  exit 1
fi

case "$MODE" in
  coding|research|private) ;;
  *)
    echo "ERROR: invalid mode '$MODE' (expected coding|research|private)" >&2
    exit 2
    ;;
esac

PROFILE=".mcp.json.$MODE"
if [[ ! -f "$PROFILE" ]]; then
  echo "ERROR: profile not found: $PROFILE" >&2
  exit 3
fi

if [[ -e ".mcp.json" && ! -L ".mcp.json" ]]; then
  echo "ERROR: .mcp.json exists and is not a symlink; refusing to overwrite" >&2
  exit 4
fi

ln -sfn "$PROFILE" .mcp.json

echo "✅ switched MCP mode: $MODE"
echo "   .mcp.json -> $(readlink .mcp.json)"
