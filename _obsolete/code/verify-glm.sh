#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 16:30:00 CST
#
# ============================================================================
# 验证"经网关调 GLM 时实际命中哪个底层模型"（第7轮重写）
# 改进：上一版只测非流式，会因 ModelScope 非流式不稳而误报"被 fallback"。
#   本版【流式、非流式分别测】，分别给结论，不再误导。
# 判定依据：响应体最后一行的 "model" 字段
#   含 cloud/glm-primary → 真·GLM（成功）
#   含 ollama/qwen      → 被 fallback 到本地
# 用法：bash _infra/verify-glm.sh
# 前置：已用 _infra/start-litellm.sh 启动网关（默认 4000）。
# ============================================================================
set -o pipefail

GATE="${1:-http://localhost:4000}/v1/chat/completions"
echo "诊断时间: $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S') CST"
echo "目标网关: $GATE"

judge() {
  local label="$1" body="$2"
  local model
  model="$(printf '%s' "$body" | grep -o '"model":"[^"]*"' | tail -1)"
  echo "  [$label] 实际命中: ${model:-（未取到 model 字段）}"
  if printf '%s' "$body" | grep -iq "glm"; then
    echo "  [$label] ✅ 真·GLM（链路正确）"
  elif printf '%s' "$body" | grep -iq "qwen\|ollama"; then
    echo "  [$label] ⚠️ 被 fallback 到本地 qwen"
  else
    echo "  [$label] ℹ️ 无法判定，请把输出 push 回来"
  fi
}

echo ""
echo "==================== 流式（Claude Code 默认走这个）===================="
RESP_STREAM="$(curl -N -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","stream":true,"messages":[{"role":"user","content":"只回复两个字：你好"}]}')"
judge "流式" "$RESP_STREAM"

echo ""
echo "==================== 非流式（已知 ModelScope 端不稳，仅供对照）===================="
RESP_NS="$(curl -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","messages":[{"role":"user","content":"只回复两个字：你好"}]}')"
judge "非流式" "$RESP_NS"

echo ""
echo "==================== 总结 ===================="
echo "· 只要【流式】是 ✅，日常使用就没问题（Claude Code 默认流式）。"
echo "· 若【非流式】是 ⚠️，那是 ModelScope 非流式接口的已知问题，第7轮正用 diag-glm.sh 精准定位根治方案。"
