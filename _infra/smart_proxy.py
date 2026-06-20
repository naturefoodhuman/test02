# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 23:55:00

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
from contextlib import asynccontextmanager

# 注入项目路径
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import SERVER_COMMANDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("SmartProxy")

# 全局持久化客户端，防止 IncompleteRead
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # 增加连接池大小和超时时间
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    http_client = httpx.AsyncClient(limits=limits, timeout=600.0)
    yield
    await http_client.aclose()

app = FastAPI(title="FORGE Smart Proxy Gatekeeper", lifespan=lifespan)

MODEL_PORT_MAP = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "claude-3-5-sonnet-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

def ensure_server(port: int):
    """工业级按需加载：探测 -> 拉起 -> 深度就绪检查"""
    # 检查端口
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return True

    if port not in SERVER_COMMANDS:
        return False

    logger.info(f"📡 目标端口 {port} 离线，正在按需拉起模型服务...")
    subprocess.Popen(SERVER_COMMANDS[port], shell=True, executable="/bin/bash")
    
    # 深度就绪检查循环
    start_time = time.time()
    while time.time() - start_time < 90: # 最多等 90 秒
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    # 端口开了，尝试发起一个真实 API 请求确认内部逻辑就绪
                    try:
                        r = httpx.get(f"http://127.0.0.1:{port}/v1/models", timeout=2.0)
                        if r.status_code == 200:
                            logger.info(f"✅ 后端 {port} 已通过 API 响应测试，准备放行请求")
                            time.sleep(2) # 最后的稳定性冗余
                            return True
                    except:
                        pass
        except:
            pass
        time.sleep(3)
        logger.info(f"   ...仍在等待 {port} 加载权重")
    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_proxy(request: Request, path: str):
    global http_client
    
    body_content = await request.body()
    target_port = None
    
    if request.method == "POST" and body_content:
        try:
            body_json = json.loads(body_content)
            model_name = body_json.get("model", "")
            target_port = MODEL_PORT_MAP.get(model_name)
        except:
            pass

    if target_port:
        if not ensure_server(target_port):
            raise HTTPException(status_code=504, detail=f"Backend {target_port} failed to ready in time")

    # 转发到内部核心网关 4001
    target_url = f"http://127.0.0.1:4001/{path}"
    
    # 复制并清理头
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # 构建转发请求
    rp_req = http_client.build_request(
        method=request.method,
        url=target_url,
        headers=headers,
        params=request.query_params,
        content=body_content
    )
    
    rp_resp = await http_client.send(rp_req, stream=True)
    
    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=dict(rp_resp.headers),
        background=httpx.Response.aclose(rp_resp) # 确保流关闭
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info", access_log=False)
