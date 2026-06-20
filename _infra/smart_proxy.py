# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 00:30:00

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
from fastapi.responses import StreamingResponse, Response

FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import SERVER_COMMANDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SmartProxy")

# 使用全局持久客户端
http_client = httpx.AsyncClient(timeout=600.0, limits=httpx.Limits(max_keepalive_connections=20))

app = FastAPI(title="FORGE Smart Proxy (Stable Build)")

MODEL_PORT_MAP = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "claude-3-5-sonnet-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

def ensure_server(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return True

    if port not in SERVER_COMMANDS:
        return False

    logger.info(f"📡 端口 {port} 离线，正在拉起...")
    subprocess.Popen(SERVER_COMMANDS[port], shell=True, executable="/bin/bash")
    
    start_time = time.time()
    while time.time() - start_time < 120:
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/v1/models", timeout=2.0)
            if r.status_code == 200:
                logger.info(f"✅ 后端 {port} 就绪")
                time.sleep(3) # 缓冲
                return True
        except:
            pass
        time.sleep(4)
        logger.info(f"   ...正在加载 (已等待 {int(time.time()-start_time)}s)")
    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_proxy(request: Request, path: str):
    body_content = await request.body()
    target_port = None
    is_stream = False
    
    if request.method == "POST" and body_content:
        try:
            body_json = json.loads(body_content)
            target_port = MODEL_PORT_MAP.get(body_json.get("model", ""))
            is_stream = body_json.get("stream", False)
        except:
            pass

    if target_port:
        if not ensure_server(target_port):
            raise HTTPException(status_code=504, detail="Backend Timeout")

    # 核心转发逻辑
    target_url = f"http://127.0.0.1:4001/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]}
    
    try:
        if is_stream:
            # 流式转发
            logger.info(f"🌊 流式转发: {path}")
            req = http_client.build_request(request.method, target_url, headers=headers, content=body_content)
            resp = await http_client.send(req, stream=True)
            return StreamingResponse(resp.aiter_raw(), status_code=resp.status_code, headers=dict(resp.headers))
        else:
            # 【重要】非流式请求采用全量缓冲转发，解决 IncompleteRead
            logger.info(f"📦 缓冲转发: {path}")
            resp = await http_client.request(request.method, target_url, headers=headers, content=body_content)
            return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
    except Exception as e:
        logger.error(f"❌ 代理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
