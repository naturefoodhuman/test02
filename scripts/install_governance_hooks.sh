#!/usr/bin/env bash
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -d .git ]; then
  echo "ERROR: .git directory not found. Run from a git checkout." >&2
  exit 1
fi

mkdir -p .git/hooks
cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec "$ROOT/scripts/hooks/pre_commit_governance.sh"
HOOK
chmod +x .git/hooks/pre-commit

echo "✅ Installed governance pre-commit hook -> .git/hooks/pre-commit"
echo "   It runs: python3 scripts/governance_check.py --strict --no-write && git diff --check"
