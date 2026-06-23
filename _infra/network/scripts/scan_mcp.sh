#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-23 10:24:12

# Run mcp-scan via the FORGE Network parser.
# Usage:
#   _infra/network/scripts/scan_mcp.sh [--target mcp-servers/name]
#   _infra/network/scripts/scan_mcp.sh --lockfile config/mcp_lockfile.yaml

set -euo pipefail

if [[ -n "${FORGE_ROOT:-}" ]]; then
  ROOT="$FORGE_ROOT"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python -m _infra.network.mcp_guard.scanner "$@"
