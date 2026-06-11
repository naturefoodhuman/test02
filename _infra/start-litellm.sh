#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 15:10:00 CST
#
# ============================================================================
# FORGE Factory · LiteLLM 启动脚本（第5轮新增）
# 解决的根因：litellm 配置里 api_key: os.environ/GLM_API_KEY 需要进程环境里真的有这个变量。
#   光 `source _infra/.env` 默认不 export，子进程 litellm 继承不到 → Missing credentials。
#   本脚本显式 export .env 里的所有变量，再启动 litellm，彻底消除这个坑。
#
# 用法：
#   source ~/.venv/bin/activate           # 先激活装了 litellm 的 venv
#   bash _infra/start-litellm.sh          # 启动网关（端口默认 4000）
#   bash _infra/start-litellm.sh 4000     # 也可显式指定端口
# ============================================================================
set -o pipefail

FORGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$FORGE_ROOT/_infra/.env"
CONFIG="$FORGE_ROOT/_infra/litellm-config.yaml"
PORT="${1:-4000}"

# 1) 检查 litellm 是否在 PATH（最常见错误：忘了激活 venv）
if ! command -v litellm >/dev/null 2>&1; then
  echo "❌ 找不到 litellm 命令。请先激活装了它的 venv，例如：source ~/.venv/bin/activate"
  exit 1
fi

# 2) 加载并 export .env（关键修复）
if [ -f "$ENV_FILE" ]; then
  echo "📥 从 $ENV_FILE 加载并 export 环境变量..."
  # 只处理形如 KEY=VALUE 的非注释行；用 set -a 让随后所有赋值自动 export
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
else
  echo "⚠️  未找到 $ENV_FILE（cp _infra/.env.example _infra/.env 并填值）"
fi

# 3) 自检 GLM_API_KEY 是否真的进了环境
if [ -n "${GLM_API_KEY:-}" ] && [ "${GLM_API_KEY:-}" != "在此填入你的 ModelScope SDK Token" ]; then
  echo "✅ GLM_API_KEY 已加载到环境（长度 ${#GLM_API_KEY}）"
else
  echo "⚠️  GLM_API_KEY 未设置或仍是占位符 → GLM 调用会 Missing credentials（仅本地模型可用）"
fi

# 4) 启动网关
echo "🚀 启动 LiteLLM：config=$CONFIG port=$PORT"
exec litellm --config "$CONFIG" --port "$PORT"
