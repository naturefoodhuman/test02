#!/bin/bash
# Smart Proxy 诊断脚本 v1.0

LOG_FILE="/tmp/forge_diagnose_$(date +%Y%m%d_%H%M%S).log"
echo "=== FORGE Smart Proxy 诊断报告 $(date) ===" | tee $LOG_FILE

echo -e "\n[1] 检查 4000 端口 (Smart Proxy)" | tee -a $LOG_FILE
lsof -i :4000 2>/dev/null | tee -a $LOG_FILE || echo "4000 端口未监听" | tee -a $LOG_FILE

echo -e "\n[2] 检查 8080 端口 (Qwen 模型)" | tee -a $LOG_FILE
lsof -i :8080 2>/dev/null | tee -a $LOG_FILE || echo "8080 端口未监听" | tee -a $LOG_FILE

echo -e "\n[3] 测试 Smart Proxy /v1/models" | tee -a $LOG_FILE
curl -s --max-time 5 http://127.0.0.1:4000/v1/models 2>&1 | tee -a $LOG_FILE

echo -e "\n[4] 测试直接模型 /v1/models (8080)" | tee -a $LOG_FILE
curl -s --max-time 5 http://127.0.0.1:8080/v1/models 2>&1 | tee -a $LOG_FILE

echo -e "\n[5] 测试 Smart Proxy chat/completions" | tee -a $LOG_FILE
curl -s --max-time 10 -X POST http://127.0.0.1:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"mtplx-qwen36-27b","messages":[{"role":"user","content":"你好"}],"max_tokens":20}' 2>&1 | tee -a $LOG_FILE

echo -e "\n=== 诊断结束 ===" | tee -a $LOG_FILE
echo "日志已保存到: $LOG_FILE"
