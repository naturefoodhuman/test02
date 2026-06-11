#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 12:30:00 CST
#
# ============================================================================
# GLM 链路诊断脚本（第4轮新增）
# 用途：把 ModelScope-GLM 经 LiteLLM 的各种调用结果统一收集到一个文件，
#       老板跑完后把该文件 git push 上来，我据此分析（无需手动粘贴）。
# 用法：
#   source _infra/.env                       # 确保 GLM_API_KEY 在环境里
#   bash _infra/diag-glm.sh > diag-glm-output.txt 2>&1
#   git add diag-glm-output.txt && git commit -m "glm diag" && git push
# 前置：LiteLLM 已在 localhost:4000 运行（source ~/.venv/bin/activate 后启动）。
# ============================================================================
set -o pipefail

GATE="http://localhost:4000/v1/chat/completions"
MS="https://api-inference.modelscope.cn/v1/chat/completions"
line() { echo ""; echo "==================== $* ===================="; }

echo "诊断时间: $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S') CST"
echo "GLM_API_KEY 是否设置: $([ -n "$GLM_API_KEY" ] && echo yes || echo NO)"

line "T1 直连 ModelScope（非流式，基准）"
time curl -s -m 60 "$MS" \
  -H "Authorization: Bearer $GLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"ZhipuAI/GLM-5","messages":[{"role":"user","content":"你好"}]}'

line "T2 直连 ModelScope（流式）"
time curl -N -s -m 60 "$MS" \
  -H "Authorization: Bearer $GLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"ZhipuAI/GLM-5","stream":true,"messages":[{"role":"user","content":"你好"}]}'

line "T3 经网关 cloud/glm-debug（无 fallback，会暴露真实错误）"
time curl -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-debug","messages":[{"role":"user","content":"你好"}]}'

line "T4 经网关 cloud/glm-primary（流式）"
time curl -N -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","stream":true,"messages":[{"role":"user","content":"你好"}]}'

line "T5 经网关 cloud/glm-primary（非流式，对照原问题）"
time curl -s -m 90 "$GATE" \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","messages":[{"role":"user","content":"你好"}]}'

line "DONE"
echo "请把本输出文件 git push 到仓库，我来分析。"
