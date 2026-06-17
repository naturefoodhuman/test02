#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
#
# 项目级 lint 命令（pre-commit Hook 调用）。
set -u

# ── Python：优先 ruff，没有则跳过（不阻塞）──
if command -v ruff >/dev/null 2>&1; then
  ruff check src tests
  exit $?
fi

echo "ℹ️  未安装 ruff，跳过 lint（建议：uv pip install ruff）"
exit 0
