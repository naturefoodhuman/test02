# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 18:30:00

import sys
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import logging

# 注入项目路径
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import _ensure_server_running

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE Smart Proxy Gatekeeper")

# 模型到端口的 SSOT 映射
MODEL_PORT_MAP = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "claude-3-5-sonnet-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_proxy(request: Request, path: str):
    # 1. 拦截解析模型请求
    target_port = None
    if request.method == "POST":
        try:
            body = await request.json()
            model_name = body.get("model", "")
            target_port = MODEL_PORT_MAP.get(model_name)
        except:
            pass

    # 2. 如果是已知模型且端口未开，执行“按需加载”
    if target_port:
        logger.info(f"🔍 识别到模型请求: {model_name} -> 目标端口: {target_port}")
        _ensure_server_running(f"http://localhost:{target_port}/v1")

    # 3. 转发请求到真正的后端或 LiteLLM (如果 LiteLLM 在其他端口运行)
    # 为了简化，如果检测到是本地模型请求，我们直接代理到对应端口；
    # 如果是 API 请求，则代理到 LiteLLM (假设 LiteLLM 运行在 4001)
    
    # 这里我们采用最简单逻辑：所有请求直接转发到 LiteLLM
    # 先确保 LiteLLM 本身在 4001 端口运行
    proxy_url = f"http://localhost:4001/{path}"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 复制请求头和数据
        req_headers = dict(request.headers)
        req_headers.pop("host", None)
        
        try:
            proxy_resp = await client.request(
                method=request.method,
                url=proxy_url,
                headers=req_headers,
                params=request.query_params,
                content=await request.body()
            )
            return StreamingResponse(
                proxy_resp.aiter_raw(),
                status_code=proxy_resp.status_code,
                headers=dict(proxy_resp.headers)
            )
        except Exception as e:
            logger.error(f"❌ 转发失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
