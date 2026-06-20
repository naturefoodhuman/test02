# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 11:30:00

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
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# 注入项目路径
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import SERVER_COMMANDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE Protocol Translator Proxy")

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
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def start_backend(port: int):
    if port not in SERVER_COMMANDS: return False
    logger.info(f"📡 端口 {port} 离线，正在新建终端标签页拉起服务...")
    # AppleScript: 在当前窗口新建标签页并执行
    script = f'tell application "Terminal" to tell (make new tab at window 1) to do script "{SERVER_COMMANDS[port]}"'
    subprocess.run(["osascript", "-e", script])
    
    start_time = time.time()
    while time.time() - start_time < 120:
        if is_listening(port):
            try:
                # 最后的可用性握手
                with httpx.Client() as client:
                    if client.get(f"http://127.0.0.1:{port}/v1/models", timeout=2).status_code == 200:
                        logger.info(f"✅ 后端 {port} 就绪")
                        return True
            except: pass
        time.sleep(4)
    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def protocol_translator(request: Request, path: str):
    body = await request.body()
    model_name = "unknown"
    target_port = 8080 # 默认
    
    # 1. 解析请求类型与目标模型
    is_anthropic = "messages" in path
    try:
        data = json.loads(body)
        model_name = data.get("model", "")
        target_port = MODEL_MAP.get(model_name, 8080)
    except: pass

    # 2. 按需拉起
    if not is_listening(target_port):
        if not start_backend(target_port):
            raise HTTPException(status_code=504, detail="Backend Startup Timeout")

    # 3. 准备转发（统一转为 OpenAI 格式发给后端）
    # 如果是 Anthropic 格式，手动提取消息
    if is_anthropic:
        logger.info(f"🔄 正在转换 Anthropic 请求 -> OpenAI 格式 (模型: {model_name})")
        openai_messages = []
        if "system" in data:
            openai_messages.append({"role": "system", "content": data["system"]})
        for msg in data.get("messages", []):
            content = msg["content"]
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
            openai_messages.append({"role": msg["role"], "content": content})
        
        forward_payload = {
            "model": "Qwen3.6-27B-MTPLX-Optimized-Quality" if target_port == 8080 else model_name,
            "messages": openai_messages,
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 4096),
            "stream": False # 强制非流式以保证稳定性
        }
    else:
        forward_payload = data

    # 4. 执行转发
    target_url = f"http://127.0.0.1:{target_port}/v1/chat/completions"
    logger.info(f"➡️ 转发至后端: {target_url}")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            resp = await client.post(target_url, json=forward_payload)
            result = resp.json()
            
            # 5. 响应翻译：如果是 Claude Code 调用的，必须转回 Anthropic 格式
            if is_anthropic:
                logger.info("🔄 正在将响应转回 Anthropic 格式...")
                answer = result['choices'][0]['message']['content']
                anthropic_resp = {
                    "id": f"msg_{uuid.uuid4().hex}",
                    "type": "message",
                    "role": "assistant",
                    "model": model_name,
                    "content": [{"type": "text", "text": answer}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 0, "output_tokens": 0} # 简化处理
                }
                return JSONResponse(content=anthropic_resp)
            else:
                return JSONResponse(content=result)
                
        except Exception as e:
            logger.error(f"❌ 转发失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
