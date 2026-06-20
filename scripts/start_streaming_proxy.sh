#!/bin/bash
# 启动流式 Smart Proxy（v5.0）

pkill -f "python3.*smart_proxy"

cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "🚀 启动 Smart Proxy 流式版 (4000)..."
nohup python3 _infra/smart_proxy_streaming.py > /tmp/forge_streaming_proxy.log 2>&1 &

sleep 4
lsof -i :4000 || echo "⚠️ 4000 端口未就绪"

echo "✅ 流式 Smart Proxy 已启动"
echo "日志: tail -f /tmp/forge_streaming_proxy.log"