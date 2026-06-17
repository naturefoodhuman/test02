#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
#
# post-tool-use Hook：write/编辑类工具执行后自动跑测试 + 失败熔断（架构书 7.2）
# 由 Claude Code 在每次 tool-use 后调用，TOOL_NAME 由 Claude Code 注入环境。
set -u

FAIL_FILE="/tmp/.forge_fail_$(basename "$PWD")"

if echo "${TOOL_NAME:-}" | grep -qiE "(write|str_replace|create|edit)"; then
  echo "🧪 Running tests..."
  bash .claude/test-runner.sh
  TEST_EXIT=$?

  if [ $TEST_EXIT -ne 0 ]; then
    COUNT=$(cat "$FAIL_FILE" 2>/dev/null || echo 0)
    COUNT=$((COUNT + 1))
    echo $COUNT > "$FAIL_FILE"
    if [ $COUNT -ge 5 ]; then
      echo "🔴 CIRCUIT BREAKER: 连续失败 5 次，强制停止。"
      echo "   请检查错误，必要时切换更强模型或 HITL 介入。"
      echo 0 > "$FAIL_FILE"
      exit 2   # exit 2 = 强制停止 Agent
    fi
    echo "❌ Tests failed ($COUNT/5). Retrying..."
    exit 1
  else
    echo 0 > "$FAIL_FILE"   # 成功重置计数
    echo "✅ Tests passed."
  fi
fi
exit 0
