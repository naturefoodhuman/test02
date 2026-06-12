#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 02:10:00 CST
#
# HARDEN 自动安全自检（debt-collection）。
# 用法（终端A，在项目根或 debt-collection 目录均可）：
#   bash projects/debt-collection/docs/harden/security_scan.sh
set -o pipefail

# 定位到 debt-collection 项目目录
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$HERE" || exit 1
echo "🔒 HARDEN 安全自检 @ $HERE"
PASS=0; FAIL=0
ok(){ echo "  ✅ $*"; PASS=$((PASS+1)); }
bad(){ echo "  ❌ $*"; FAIL=$((FAIL+1)); }

echo "【1】.gitignore 覆盖敏感项"
for pat in "runtime/" "*.db" "data/"; do
  grep -q -- "$pat" .gitignore 2>/dev/null && ok ".gitignore 含 $pat" || bad ".gitignore 缺 $pat"
done

echo "【2】无敏感文件被 Git 跟踪"
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
  TRACKED_DB=$(git ls-files | grep -E '\.(db|sqlite)$' || true)
  [ -z "$TRACKED_DB" ] && ok "无 .db/.sqlite 被跟踪" || bad "发现被跟踪的 DB：$TRACKED_DB"
else
  echo "  ℹ️ 非 git 仓库或无 git，跳过"
fi

echo "【3】合规模块关键词覆盖（红线）"
COMP="src/debt/compliance.py"
for kw in "威胁" "爆通讯录" "查银行流水" "定位"; do
  grep -q "$kw" "$COMP" 2>/dev/null && ok "compliance 覆盖『$kw』" || bad "compliance 缺『$kw』"
done

echo "【4】策略报告强制过合规自检"
grep -q "check_text" src/debt/strategy.py 2>/dev/null && ok "strategy 调用了 check_text" || bad "strategy 未过合规自检"

echo "【5】身份证脱敏"
grep -q "def mask_id" src/debt/models.py 2>/dev/null && ok "存在 mask_id 脱敏" || bad "缺身份证脱敏"

echo "【6】免责声明 + 律师复核提示"
grep -q "免责声明" src/debt/strategy.py 2>/dev/null && ok "策略含免责声明" || bad "策略缺免责声明"

echo ""
echo "结果：通过 $PASS 项，失败 $FAIL 项"
[ $FAIL -eq 0 ] && echo "🟢 HARDEN 自动自检全部通过" || echo "🔴 有未通过项，请修复"
exit $FAIL
