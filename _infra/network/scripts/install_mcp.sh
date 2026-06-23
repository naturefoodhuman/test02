#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 22:38:00

# Install a pinned MCP server into a local, auditable path.
#
# Usage:
#   _infra/network/scripts/install_mcp.sh <server-name> <repo-url> <commit-hash>
#
# Security rules:
# - No @latest / HEAD / branch names.
# - Only git clone + exact commit checkout.
# - Dependency install uses lockfiles when present.
# - mcp-scan is required unless FORGE_MCP_INSTALL_SKIP_SCAN=1 (unit tests only).
# - Writes config/mcp_lockfile.yaml with repo, commit and local path.

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  install_mcp.sh <server-name> <repo-url> <commit-hash>

Environment:
  FORGE_ROOT                     Project root (default: git top-level)
  MCP_SERVER_ROOT                Install dir (default: $FORGE_ROOT/mcp-servers)
  MCP_LOCKFILE                   Lockfile path (default: $FORGE_ROOT/config/mcp_lockfile.yaml)
  FORGE_MCP_INSTALL_FORCE=1      Replace existing server dir
  FORGE_MCP_INSTALL_SKIP_SCAN=1  Skip mcp-scan (tests only)
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 3 ]]; then
  usage >&2
  exit 2
fi

SERVER_NAME="$1"
REPO_URL="$2"
COMMIT_HASH="$3"

if [[ ! "$SERVER_NAME" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: server-name must match ^[A-Za-z0-9._-]+$" >&2
  exit 2
fi

if [[ "$REPO_URL" == *"@latest"* || "$REPO_URL" == uvx\ * || "$REPO_URL" == *"curl | sh"* ]]; then
  echo "ERROR: forbidden MCP install source. Use pinned git repo + commit." >&2
  exit 2
fi

if [[ "$COMMIT_HASH" == "HEAD" || "$COMMIT_HASH" == "main" || "$COMMIT_HASH" == "master" || "$COMMIT_HASH" == "latest" ]]; then
  echo "ERROR: commit-hash must be an immutable git commit, not a branch/name." >&2
  exit 2
fi

if [[ ! "$COMMIT_HASH" =~ ^[0-9a-fA-F]{7,40}$ ]]; then
  echo "ERROR: commit-hash must be 7-40 hex characters." >&2
  exit 2
fi

if [[ -n "${FORGE_ROOT:-}" ]]; then
  ROOT="$FORGE_ROOT"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

SERVER_ROOT="${MCP_SERVER_ROOT:-$ROOT/mcp-servers}"
LOCKFILE="${MCP_LOCKFILE:-$ROOT/config/mcp_lockfile.yaml}"
SERVER_DIR="$SERVER_ROOT/$SERVER_NAME"

mkdir -p "$SERVER_ROOT" "$(dirname "$LOCKFILE")"

if [[ -e "$SERVER_DIR" ]]; then
  if [[ "${FORGE_MCP_INSTALL_FORCE:-0}" == "1" ]]; then
    rm -rf "$SERVER_DIR"
  else
    echo "ERROR: server dir already exists: $SERVER_DIR (set FORGE_MCP_INSTALL_FORCE=1 to replace)" >&2
    exit 3
  fi
fi

printf 'Installing MCP server %s\n' "$SERVER_NAME"
printf '  repo:   %s\n' "$REPO_URL"
printf '  commit: %s\n' "$COMMIT_HASH"
printf '  path:   %s\n' "$SERVER_DIR"

git clone "$REPO_URL" "$SERVER_DIR"
(
  cd "$SERVER_DIR"
  git checkout --detach "$COMMIT_HASH"
  actual_commit="$(git rev-parse HEAD)"
  case "$actual_commit" in
    "$COMMIT_HASH"*) ;;
    *)
      echo "ERROR: checked out commit $actual_commit does not match requested $COMMIT_HASH" >&2
      exit 4
      ;;
  esac
)

(
  cd "$SERVER_DIR"
  if [[ -f package-lock.json ]]; then
    npm ci
  elif [[ -f package.json ]]; then
    echo "ERROR: package.json present but package-lock.json missing; refusing non-reproducible npm install" >&2
    exit 5
  elif [[ -f poetry.lock && -f pyproject.toml ]]; then
    poetry install
  elif [[ -f uv.lock && -f pyproject.toml ]]; then
    uv sync --frozen
  else
    echo "No JS/Python lockfile detected; dependency install skipped."
  fi
)

SCAN_STATUS="passed"
if [[ "${FORGE_MCP_INSTALL_SKIP_SCAN:-0}" == "1" ]]; then
  SCAN_STATUS="skipped_for_test"
  echo "WARNING: mcp-scan skipped because FORGE_MCP_INSTALL_SKIP_SCAN=1"
else
  if ! command -v mcp-scan >/dev/null 2>&1; then
    echo "ERROR: mcp-scan not found. Install it first (e.g. pipx install mcp-scan)." >&2
    exit 6
  fi
  (
    cd "$SERVER_DIR"
    mcp-scan scan
  )
fi

python - "$LOCKFILE" "$SERVER_NAME" "$REPO_URL" "$COMMIT_HASH" "$SERVER_DIR" "$SCAN_STATUS" <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import yaml

lockfile = Path(sys.argv[1])
server_name = sys.argv[2]
repo_url = sys.argv[3]
commit_hash = sys.argv[4]
server_dir = sys.argv[5]
scan_status = sys.argv[6]

if lockfile.exists():
    raw = lockfile.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
else:
    data = {}

if not isinstance(data, dict):
    data = {}

data.setdefault("version", "1.0")
data.setdefault("servers", {})
data["servers"][server_name] = {
    "repo_url": repo_url,
    "commit_hash": commit_hash,
    "local_path": server_dir,
    "scan_status": scan_status,
    "installed_at": datetime.now(timezone.utc).isoformat(),
}

header = "# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode\n# 创建时间（北京时间）：2026-06-22 22:38:00\n\n"
lockfile.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=True), encoding="utf-8")
PY

printf '✅ MCP server installed and locked: %s\n' "$SERVER_NAME"
printf '   lockfile: %s\n' "$LOCKFILE"
