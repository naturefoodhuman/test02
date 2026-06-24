#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 14:55:00

# Start an isolated AI-Private Chrome profile with remote debugging enabled.
#
# Usage:
#   _infra/network/scripts/start_private_chrome.sh [profile-name] [port]
#   _infra/network/scripts/start_private_chrome.sh ai-private-github 9222
#   _infra/network/scripts/start_private_chrome.sh --print-command ai-private-github 9222

set -euo pipefail

PRINT_ONLY=0
if [[ "${1:-}" == "--print-command" ]]; then
  PRINT_ONLY=1
  shift
fi

PROFILE_NAME="${1:-ai-private-github}"
PORT="${2:-9222}"

if [[ ! "$PROFILE_NAME" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: invalid profile name: $PROFILE_NAME" >&2
  exit 2
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]]; then
  echo "ERROR: port must be numeric: $PORT" >&2
  exit 2
fi

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE_ROOT="${AI_AGENT_PROFILE_ROOT:-$HOME/ai-agent/profiles}"
USER_DATA_DIR="$PROFILE_ROOT/$PROFILE_NAME"

mkdir -p "$USER_DATA_DIR"

CMD=(
  "$CHROME_BIN"
  "--remote-debugging-port=$PORT"
  "--user-data-dir=$USER_DATA_DIR"
  "--no-first-run"
  "--no-default-browser-check"
  "--disable-extensions"
  "--disable-sync"
  "--disable-background-networking"
)

printf 'Chrome private profile: %s\n' "$PROFILE_NAME"
printf 'Remote debugging port: %s\n' "$PORT"
printf 'User data dir: %s\n' "$USER_DATA_DIR"

if [[ "$PRINT_ONLY" == "1" ]]; then
  printf '%q ' "${CMD[@]}"
  printf '\n'
  exit 0
fi

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "ERROR: Chrome binary not found or not executable: $CHROME_BIN" >&2
  echo "Set CHROME_BIN to your Chrome executable path." >&2
  exit 3
fi

"${CMD[@]}" &
CHROME_PID=$!
trap 'kill "$CHROME_PID" 2>/dev/null || true' INT TERM EXIT
wait "$CHROME_PID"
