#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
#
# 项目级测试命令（Hooks 调用）。按项目类型自定义这一处即可。
set -u

# ── Python 项目（默认）──
if [ -d tests ]; then
  python -m pytest tests/unit/ --timeout=30 -x -q
  exit $?
fi

# ── Node.js 项目示例（解开使用）──
# npm test --silent; exit $?

# ── Go 项目示例 ──
# go test ./... -timeout 30s; exit $?

echo "⚠️  未找到 tests/ 目录，跳过测试（请按项目类型配置 test-runner.sh）"
exit 0
