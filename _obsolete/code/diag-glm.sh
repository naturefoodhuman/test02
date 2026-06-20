#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 16:30:00 CST
#
# ============================================================================
# GLM 链路精准诊断脚本 v2（第7轮重写）
# 目标：分离出"非流式失败"到底是 ① ModelScope 端的问题 还是 ② LiteLLM 转发的问题。
#   关键新增：T1 直连 ModelScope【非流式】—— 这是上一版漏掉的对照项。
# 用法：
#   source ~/.venv/bin/activate
#   bash _infra/start-litellm.sh           # 另一个终端先启动网关（它会 export Key）
#   # 本终端也要有 Key：
#   set -a; . _infra/.env; set +a
#   bash _infra/diag-glm.sh > diag-glm-v2-output.txt 2>&1
#   git add diag-glm-v2-output.txt && git commit -m "glm diag v2" && git push
# ============================================================================
set -o pipefail

GATE="http://localhost:4000/v1/chat/completions"
MS="https://api-inference.modelscope.cn/v1/chat/completions"
MODEL_MS="ZhipuAI/GLM-5"
line() { echo ""; echo "==================== $* ===================="; }
# 只取响应体最后一行的 model 字段（避免被流式刷屏）
showmodel() { grep -o '"model":"[^"]*"' | tail -1; }

echo "诊断时间: $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S') CST"
if [ -n "$GLM_API_KEY" ]; then
  echo "GLM_API_KEY 是否设置: yes (长度 ${#GLM_API_KEY})"
else
  echo "GLM_API_KEY 是否设置: NO"
  echo "⚠️ 请先在本终端执行：set -a; . _infra/.env; set +a  再重跑本脚本"
fi

# ─────────────────────────────────────────────────────────────────────
# 第一组：直连 ModelScope（绕过 LiteLLM）—— 判断 ModelScope 端本身行不行
# ─────────────────────────────────────────────────────────────────────
line "A1 直连 ModelScope【非流式】（关键对照！上一版漏了这项）"
echo "[完整响应]"
time curl -s -m 60 "$MS" \
  -H "Authorization: Bearer $GLM_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL_MS\",\"messages\":[{\"role\":\"user\",\"content\":\"只回复两个字：你好\"}]}"

line "A2 直连 ModelScope【流式】"
echo "[只显示前若干行]"
time curl -N -s -m 60 "$MS" \
  -H "Authorization: Bearer $GLM_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL_MS\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"只回复两个字：你好\"}]}" | head -5

# ─────────────────────────────────────────────────────────────────────
# 第二组：经 LiteLLM 网关 —— 判断转发层行不行
# ─────────────────────────────────────────────────────────────────────
line "B1 经网关 glm-debug【非流式】(无fallback，会暴露真实错误)"
time curl -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-debug","messages":[{"role":"user","content":"只回复两个字：你好"}]}'

line "B2 经网关 glm-primary【流式】实际命中哪个模型"
time curl -N -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","stream":true,"messages":[{"role":"user","content":"只回复两个字：你好"}]}' | showmodel

line "B3 经网关 glm-primary【非流式】实际命中哪个模型"
time curl -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","messages":[{"role":"user","content":"只回复两个字：你好"}]}' | showmodel

line "DONE — 请把 diag-glm-v2-output.txt push 回来，我据此对症修复"
echo "判读指引（给老板看）："
echo "  · A1 失败 / A2 成功 → ModelScope 非流式接口本身有问题，解法=让 LiteLLM 对该模型强制流式"
echo "  · A1 成功 / B3 失败 → 问题在 LiteLLM 转发层，另寻配置"
echo "  · A1、B3 都成功 → 之前是 Key 未加载导致的假象，现已修复"
