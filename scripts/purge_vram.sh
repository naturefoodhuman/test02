#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 15:30:00

# 强制清理所有 AI 进程，释放显存
echo -e "\033[0;34m🌊 正在强制回收 GPU 显存...\033[0m"

pkill -9 -f "mtplx"
pkill -9 -f "llama-server"
pkill -9 -f "ollama"
pkill -9 -f "uvicorn"
pkill -9 -f "litellm"

# 精准清理 4000 和 4001 端口
lsof -i tcp:4000 | awk 'NR!=1 {print $2}' | xargs kill -9 2>/dev/null
lsof -i tcp:4001 | awk 'NR!=1 {print $2}' | xargs kill -9 2>/dev/null

echo -e "\033[0;32m✅ 显存已强制释放。请重启 scripts/forge-start.sh 或 smart_proxy.py\033[0m"
