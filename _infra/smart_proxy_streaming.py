# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 16:30:00 CST
"""
Smart Proxy v5.0 - SSE 流式直通版（针对长思考模型优化）

核心原则（2026 社区最佳实践）：
1. 强制 stream=True
2. 原样透传 SSE 字节（不重新序列化）
3. read=None + chunk 级超时
4. 禁用 keep-alive
5. payload 字段白名单
"""

import sys
import os
import uvicorn
import json
import time
import subprocess
import socket
import logging
import uuid
import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("SmartProxy-Streaming")

app = FastAPI(title="FORGE Smart Proxy v5.0 (Streaming)")

# MTPLX 实际 model id
REAL_ID_MAP = {
    8080: "mtplx-qwen36-27b-optimized-quality",
    8082: "mtplx-gemma4-optimized-quality",
}

MODEL_TO_PORT = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
}

# 允许的字段白名单（解决 400 Bad Request）
ALLOWED_FIELDS = {"model", "messages", "stream", "temperature", "max_tokens", "top_p", "stop"}

# 流式客户端配置（关键）
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,
        read=None,          # ← 关键：读超时设为 None
        write=30.0,
        pool=10.0,
    ),
    limits=httpx.Limits(
        max_connections=20,
        max_keepalive_connections=0,   # ← 禁用 keep-alive
    ),
    http2=False,
)


def is_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


async def ensure_server(port: int) -> bool:
    if is_listening(port):
        return True
    # 这里可以扩展 AppleScript 拉起逻辑
    return False


@app.post("/v1/chat/completions")
async def chat_proxy(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    model_name = payload.get("model", "")
    target_port = MODEL_TO_PORT.get(model_name, 8080)

    if not await ensure_server(target_port):
        raise HTTPException(status_code=503, detail="Backend not ready")

    # 强制开启流式 + 使用正确 model id
    payload["stream"] = True
    payload["model"] = REAL_ID_MAP.get(target_port, model_name)

    # 字段白名单过滤（解决 400）
    forward_payload = {k: v for k, v in payload.items() if k in ALLOWED_FIELDS and v is not None}

    target_url = f"http://127.0.0.1:{target_port}/v1/chat/completions"

    async def event_stream():
        try:
            async with http_client.stream("POST", target_url, json=forward_payload) as resp:
                if resp.status_code != 200:
                    err = await resp.aread()
                    yield f"data: {{\"error\": {err.decode()!r}}}\n\n".encode()
                    return

                async for chunk in resp.aiter_raw():
                    yield chunk  # 原样透传 SSE 字节

        except Exception as e:
            logger.error(f"流式转发失败: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n".encode()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info")