#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:20:00

# FORGE Network backup script (E10-C3-S1-T1)
#
# Backs up MCP profiles, config, Docker network configs, and selected runtime DBs.
# It intentionally does NOT back up browser profiles, cookies, sessions,
# password stores, payment autofill, or arbitrary runtime directories.
#
# Usage:
#   scripts/backup.sh
#   scripts/backup.sh --dry-run
#   scripts/backup.sh --dest runtime/backups

set -euo pipefail

DRY_RUN=0
DEST=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --dest) DEST="${2:-}"; shift 2 ;;
    -h|--help) sed -n '1,18p' "$0"; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -n "${FORGE_ROOT:-}" ]]; then
  ROOT="$FORGE_ROOT"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
cd "$ROOT"

BACKUP_DIR="${DEST:-runtime/backups}"
DATE="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/forge-network-$DATE.tar.gz"

INCLUDE_CANDIDATES=(
  ".mcp.json"
  ".mcp.json.coding"
  ".mcp.json.research"
  ".mcp.json.private"
  "config"
  "docker"
  "runtime/audit.db"
  "runtime/rag.db"
  "runtime/pii_map.db"
)

EXCLUDES=(
  "profiles"
  "profiles/**"
  "runtime/browser*"
  "runtime/sessions*"
  "runtime/cookies*"
  "**/Cookies"
  "**/Cookies-journal"
  "**/Login Data"
  "**/Web Data"
  "**/*cookie*"
  "**/*session*"
  "**/*payment*"
)

INCLUDES=()
for path in "${INCLUDE_CANDIDATES[@]}"; do
  [[ -e "$path" ]] && INCLUDES+=("$path")
done

if [[ ${#INCLUDES[@]} -eq 0 ]]; then
  echo "ERROR: nothing to back up" >&2
  exit 1
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "Backup dry-run"
  echo "Destination: $BACKUP_FILE"
  printf 'Include:\n'
  printf '  %s\n' "${INCLUDES[@]}"
  printf 'Exclude:\n'
  printf '  %s\n' "${EXCLUDES[@]}"
  exit 0
fi

mkdir -p "$BACKUP_DIR"
TAR_ARGS=("-czf" "$BACKUP_FILE")
for pattern in "${EXCLUDES[@]}"; do
  TAR_ARGS+=("--exclude=$pattern")
done
TAR_ARGS+=("${INCLUDES[@]}")

tar "${TAR_ARGS[@]}"

if tar -tzf "$BACKUP_FILE" | grep -E '(Cookies|Login Data|Web Data|cookie|session|payment)' >/dev/null; then
  echo "ERROR: backup archive contains forbidden browser/session material" >&2
  rm -f "$BACKUP_FILE"
  exit 3
fi

SIZE="$(du -h "$BACKUP_FILE" | cut -f1)"
echo "✅ backup created: $BACKUP_FILE ($SIZE)"
find "$BACKUP_DIR" -name 'forge-network-*.tar.gz' -type f -mtime +30 -delete 2>/dev/null || true
