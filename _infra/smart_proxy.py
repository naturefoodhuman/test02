# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 02:30:00

import sys
import os
import uvicorn
import json
import time
import subprocess
import socket
import logging
import litellm
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

# 注入项目路径
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE Smart Proxy (Mac Terminal Edition)")

# 服务器指令注册表
SERVER_COMMANDS = {
    8080: "cd ~/LocalAI/servers && uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080",
    8082: "cd ~/LocalAI/servers && uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082",
    8084: "llama-server -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2",
}

# 模型到端口映射
MODEL_MAP = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "claude-3-5-sonnet-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

def is_listening(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0

def start_in_new_terminal(port: int):
    """使用 AppleScript 在新终端标签页中拉起模型 (R11 最佳实践)"""
    if port not in SERVER_COMMANDS:
        return False
    
    cmd = SERVER_COMMANDS[port]
    logger.info(f"📡 端口 {port} 离线，正在新建 Terminal 标签页运行指令...")
    
    # AppleScript 指令：打开新标签页并执行
    script = f'tell application "Terminal" to do script "{cmd}"'
    subprocess.run(["osascript", "-e", script])
    
    # 深度就绪检查
    start_time = time.time()
    while time.time() - start_time < 150: # 宽限 2.5 分钟
        if is_listening(port):
            # 端口开了，再尝试 API 握手
            try:
                import requests
                r = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=2)
                if r.status_code == 200:
                    logger.info(f"✅ 后端 {port} 已就绪")
                    return True
            except:
                pass
        time.sleep(5)
        logger.info(f"   ...正在等待 {port} 加载权重 (已耗时 {int(time.time()-start_time)}s)")
    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_proxy(request: Request, path: str):
    body_content = await request.body()
    model_name = "unknown"
    target_port = None
    
    if request.method == "POST" and body_content:
        try:
            body_json = json.loads(body_content)
            model_name = body_json.get("model", "")
            target_port = MODEL_MAP.get(model_name)
        except:
            pass

    # 1. 按需拉起模型 (Terminal 开窗)
    if target_port:
        if not is_listening(target_port):
            if not start_in_new_terminal(target_port):
                raise HTTPException(status_code=504, detail="Model Loading Timeout")

    # 2. 直接调用 LiteLLM 库进行请求 (不经过 4001 中转，稳如泰山)
    if request.method == "POST" and "chat/completions" in path:
        logger.info(f"➡️ 调用 LiteLLM 转发 {model_name} 至本地端口 {target_port}")
        try:
            # 准备 LiteLLM 参数
            params = json.loads(body_content)
            # 修正 api_base
            api_base = f"http://127.0.0.1:{target_port}/v1"
            
            # 使用 litellm 进行协议转换并请求
            response = await litellm.acompletion(
                **params,
                api_base=api_base,
                custom_llm_provider="openai"
            )
            # 将 LiteLLM 响应转回 FastAPI 响应
            return response
        except Exception as e:
            logger.error(f"❌ LiteLLM 核心调用失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "Proxy is alive. Use POST /v1/chat/completions for model requests."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
