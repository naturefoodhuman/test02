#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
#
# pre-commit Hook：lint 检查 + TASK_GRAPH 状态检查（架构书 7.2）
set -u

echo "🔍 Running lint..."
bash .claude/lint-runner.sh
if [ $? -ne 0 ]; then
  echo "❌ Lint failed. Fix before committing."
  exit 1
fi

# TASK_GRAPH 不得有 IN_PROGRESS（防止任务图腐化，风险#3）
if grep -q "status: IN_PROGRESS" docs/TASK_GRAPH.md 2>/dev/null; then
  echo "❌ TASK_GRAPH 存在 IN_PROGRESS 任务。提交前请把状态更新为 DONE。"
  exit 1
fi

echo "✅ Pre-commit checks passed."
exit 0
