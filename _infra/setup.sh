#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
#
# ============================================================================
# FORGE Factory · 一键环境初始化与自检（目标环境：macOS M1 Max）
# 用法：bash _infra/setup.sh          # 自检 + 提示
#       bash _infra/setup.sh --check  # 仅自检（不安装）
# 设计：幂等、可重复跑；只检查与提示，不擅自安装破坏性的东西。
# 满足需求书 8.5（中国网络适配，每步带验证命令）。
# ============================================================================
# 注意：自检脚本不用 set -u（避免在 macOS 自带老 bash 上因参数展开误触 unbound 退出）
# 自检脚本的职责是"发现并报告问题"，不应自己先崩。
set -o pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
err()  { echo -e "${RED}❌ $*${NC}"; }
hr()   { echo "----------------------------------------------------------------"; }

FORGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "FORGE_ROOT = $FORGE_ROOT"
hr

# 1. Python ----------------------------------------------------------------
echo "【1/7】检查 Python（需求：3.11）"
if command -v python3 >/dev/null 2>&1; then
  ok "$(python3 --version)"
else
  err "未找到 python3"
fi
hr

# 2. uv 包管理器 -----------------------------------------------------------
echo "【2/7】检查 uv 包管理器（需求强制用 uv）"
if command -v uv >/dev/null 2>&1; then
  ok "$(uv --version)"
else
  warn "未找到 uv。安装（官方）：curl -LsSf https://astral.sh/uv/install.sh | sh"
  warn "国内网络慢可改用：pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple"
fi
hr

# 3. Ollama 本地模型 -------------------------------------------------------
echo "【3/7】检查 Ollama 与本地模型（C3/C4）"
if command -v ollama >/dev/null 2>&1; then
  # ollama --version 在服务未启动时会打印 Warning，需要单独判断版本是否真的拿到
  OLLAMA_VER="$(ollama --version 2>/dev/null | grep -i 'version' | head -1)"
  if [ -n "$OLLAMA_VER" ]; then
    ok "$OLLAMA_VER"
  else
    warn "ollama 已安装，但服务似乎未启动（另开终端运行：ollama serve）"
  fi

  echo "已拉取的模型："
  OLLAMA_LIST="$(ollama list 2>/dev/null)"
  if [ -n "$OLLAMA_LIST" ]; then
    echo "$OLLAMA_LIST"
  else
    warn "无法列出模型（ollama 服务可能未启动：ollama serve）"
  fi

  # 直接用全量 tag 在列表里查找，避免任何参数展开/子 shell 切割导致的编码乱码
  for model_tag in "qwen3.6:35b-a3b-q8_0" "qwen3:14b"; do
    if echo "$OLLAMA_LIST" | grep -q "$model_tag"; then
      ok "已发现模型：$model_tag"
    else
      warn "未发现模型：$model_tag（拉取：ollama pull $model_tag）"
    fi
  done
else
  warn "未找到 ollama。安装见 https://ollama.com 或 brew install ollama"
fi
hr

# 4. LiteLLM 网关 ----------------------------------------------------------
echo "【4/7】检查 LiteLLM"
if command -v litellm >/dev/null 2>&1; then
  ok "litellm 已安装（在当前 PATH 中）"
else
  # litellm 常被装在某个 venv 里（如 ~/.venv）。这里探测常见位置，给出更准确的提示，
  # 避免"明明能启动却报未找到"的误导。
  FOUND_LITELLM=""
  for cand in "$HOME/.venv/bin/litellm" "$FORGE_ROOT/.venv/bin/litellm" "./.venv/bin/litellm"; do
    if [ -x "$cand" ]; then FOUND_LITELLM="$cand"; break; fi
  done
  if [ -n "$FOUND_LITELLM" ]; then
    ok "litellm 已安装于 venv：$FOUND_LITELLM"
    warn "当前终端未激活该 venv，故 PATH 里找不到。启动网关前先：source $(dirname "$(dirname "$FOUND_LITELLM")")/bin/activate"
  else
    warn "未找到 litellm（PATH 与常见 venv 均无）。安装：uv pip install 'litellm[proxy]'"
    warn "国内源：uv pip install 'litellm[proxy]' -i https://pypi.tuna.tsinghua.edu.cn/simple"
    warn "提示：若你已在某个 venv 里装过，激活它即可（source <venv>/bin/activate）。"
  fi
fi
echo "启动网关：litellm --config $FORGE_ROOT/_infra/litellm-config.yaml --port 4000"
hr

# 5. .env -----------------------------------------------------------------
echo "【5/7】检查 .env"
if [ -f "$FORGE_ROOT/_infra/.env" ]; then
  ok "_infra/.env 存在"
  grep -q "GLM_API_KEY=\"在此填入" "$FORGE_ROOT/_infra/.env" 2>/dev/null && \
    warn "GLM_API_KEY 仍是占位符，记得填真实 Key" || ok "GLM_API_KEY 已修改（未校验有效性）"
else
  warn "未找到 _infra/.env。执行：cp _infra/.env.example _infra/.env 然后填值"
fi
hr

# 6. Git ------------------------------------------------------------------
echo "【6/7】检查 Git（NFR-009：知识/决策以纯文本存于 Git）"
if command -v git >/dev/null 2>&1; then
  ok "$(git --version)"
else
  err "未找到 git"
fi
hr

# 7. forge 骨架 -----------------------------------------------------------
echo "【7/7】检查 forge 目录骨架"
for d in _infra _factory _factory/skills _factory/patterns _factory/lessons _agents projects; do
  if [ -d "$FORGE_ROOT/$d" ]; then ok "$d/"; else err "缺失目录 $d/"; fi
done
hr

echo ""
echo "下一步建议："
echo "  1) cp _infra/.env.example _infra/.env 并填 GLM_API_KEY"
echo "  2) ollama serve（另开一个终端）"
echo "  3) litellm --config _infra/litellm-config.yaml --port 4000"
echo "  4) 按 docs/REAL_MACHINE_VALIDATION.md 逐项验证链路"
echo "  5) chmod +x _infra/*.sh _agents/.. 等脚本（首次）"
ok "自检完成。"
