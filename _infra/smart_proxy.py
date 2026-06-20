# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 23:30:00

import sys
import os
import uvicorn
import json
import time
import subprocess
import socket
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

# 注入项目路径
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE Smart Proxy Gatekeeper")

# 服务器启动指令注册表
SERVER_COMMANDS = {
    8080: "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080 > /tmp/mtplx_8080.log 2>&1 &",
    8082: "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082 > /tmp/mtplx_8082.log 2>&1 &",
    8084: "nohup llama-server -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > /tmp/llama_8084.log 2>&1 &",
}

# 模型到端口的映射
MODEL_PORT_MAP = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "claude-3-5-sonnet-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

def wait_for_backend(port: int, timeout: int = 60):
    """等待后端不仅是端口开启，还要能响应请求"""
    start_time = time.time()
    logger.info(f"⏳ 等待后端端口 {port} 就绪...")
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    # 端口开了，再尝试发一个轻量请求确认应用已启动
                    try:
                        # 尝试访问 /v1/models 或根路径
                        resp = httpx.get(f"http://127.0.0.1:{port}/v1/models", timeout=2.0)
                        if resp.status_code == 200:
                            logger.info(f"✅ 后端 {port} 已完全就绪")
                            return True
                    except:
                        pass
        except:
            pass
        time.sleep(2)
        logger.info(f"   ...仍在等待端口 {port}")
    return False

def ensure_server(port: int):
    """确保服务器运行，没开就拉起"""
    if port not in SERVER_COMMANDS:
        return True
    
    # 检查端口
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return True # 已在运行

    logger.info(f"📡 检测到端口 {port} 未启动，正在按需拉起...")
    subprocess.Popen(SERVER_COMMANDS[port], shell=True, executable="/bin/bash")
    return wait_for_backend(port)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_proxy(request: Request, path: str):
    # 1. 解析模型请求
    body_content = await request.body()
    target_port = None
    model_name = "unknown"
    
    if request.method == "POST" and body_content:
        try:
            body_json = json.loads(body_content)
            model_name = body_json.get("model", "")
            target_port = MODEL_PORT_MAP.get(model_name)
        except:
            pass

    # 2. 按需加载
    if target_port:
        logger.info(f"🎯 识别到模型: {model_name} -> 目标端口: {target_port}")
        if not ensure_server(target_port):
            logger.error(f"❌ 无法启动后端服务器 (Port: {target_port})")
            raise HTTPException(status_code=503, detail=f"Backend server (port {target_port}) failed to start")

    # 3. 转发到 LiteLLM (4001 端口)
    # 补全路径，确保 /v1/chat/completions 这种路径被正确处理
    # 如果 path 已经包含 v1，就不再加前缀
    target_url = f"http://127.0.0.1:4001/{path}"
    
    logger.info(f"➡️ 转发请求至 LiteLLM: {target_url}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        req_headers = dict(request.headers)
        # 移除可能引起冲突的头
        req_headers.pop("host", None)
        req_headers.pop("content-length", None)

        try:
            proxy_resp = await client.request(
                method=request.method,
                url=target_url,
                headers=req_headers,
                params=request.query_params,
                content=body_content
            )
            
            return StreamingResponse(
                proxy_resp.aiter_raw(),
                status_code=proxy_resp.status_code,
                headers=dict(proxy_resp.headers)
            )
        except httpx.ConnectError:
            logger.error("❌ 无法连接到 LiteLLM (4001)。请确保 forge-start.sh 已拉起网关。")
            raise HTTPException(status_code=502, detail="LiteLLM gateway (port 4001) is not running")
        except Exception as e:
            logger.error(f"❌ 代理异常: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 FORGE Smart Proxy 启动在 4000 端口...")
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info")
