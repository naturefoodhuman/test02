# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 17:30:00

import os
import sys
import time
import subprocess
import socket
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
import httpx

# 导入按需加载逻辑 (复用 llm_client 的配置)
sys.path.append(os.path.join(os.path.dirname(__file__), "../_factory/patterns/peer-review/src"))
from peer_review.llm_client import _ensure_server_running

app = FastAPI(title="FORGE Smart Gateway Gatekeeper")

# 端口映射表
PORT_MAPPING = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "claude-3-5-sonnet-20241022": 8080, # 映射到主大脑
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_gatekeeper(request: Request, path: str):
    # 1. 尝试从请求体获取模型名
    body = await request.json() if request.method == "POST" else {}
    model_name = body.get("model", "")
    
    # 2. 如果是模型请求，触发“按需加载”
    target_port = PORT_MAPPING.get(model_name)
    if target_port:
        base_url = f"http://localhost:{target_port}/v1"
        # 调用 llm_client 里的拉起逻辑
        _ensure_server_running(base_url)

    # 3. 转发请求到真实的 LiteLLM (内部端口 4001) 或直接转发到后端
    # 这里我们采用最稳妥的方式：让 Gatekeeper 代理请求
    # 实际上为了性能，我们可以让 LiteLLM 跑在 4001，Gatekeeper 跑在 4000
    # 但为了简化，这里我们先确保模型拉起，然后直接让 LiteLLM 处理后续。
    
    # 注意：为了不重写 LiteLLM，我们采取“拦截-启动-放行”策略。
    # 我们让真正的 LiteLLM 随后在 4000 启动，这个 Gatekeeper 仅用于 CLI 启动前的预热或集成到 LiteLLM 的 Custom Callback。
    return {"status": "ready"}

if __name__ == "__main__":
    # 实际上，更好的工业做法是使用 LiteLLM 的 Custom Callbacks。
    # 考虑到老板的使用便利性，我直接修改 llm_client 并让 LiteLLM 通过 Python 模式启动。
    pass
