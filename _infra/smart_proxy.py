# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 17:45:00

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
from fastapi.responses import StreamingResponse, JSONResponse
from threading import Lock

# 注入项目路径
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import SERVER_COMMANDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE VRAM-Aware Unified Gateway")

# 显存管理 SSOT (M1 Max 64G 优化)
VRAM_LIMIT = 48 # GB
MODEL_VRAM_MAP = {
    8080: 20, # Qwen 27B
    8082: 16, # Gemma4
    8084: 36, # Qwopus 35B
    11434: 20, # Ollama Models (Default 20G for tracking)
}
active_servers = {} # {port: last_used_time}
vram_lock = Lock()

# 服务器启动指令补充 (如缺失)
if 11434 not in SERVER_COMMANDS:
    SERVER_COMMANDS[11434] = "ollama serve"

MODEL_MAP = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "local-qwen35b": 8080,
    "local-deepseek-r1": 11434,
    "claude-3-5-sonnet-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-3-5-sonnet-latest": 8080
}

def is_listening(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def purge_oldest_server():
    if not active_servers: return
    # 找出一个正在运行的最久未使用的端口
    running_active = {p: t for p, t in active_servers.items() if is_listening(p)}
    if not running_active: return
    
    oldest_port = min(running_active, key=running_active.get)
    logger.info(f"⚠️ 显存不足，正在卸载最久未使用的模型 (Port {oldest_port})...")
    subprocess.run(f"pkill -9 -f '.*{oldest_port}'", shell=True)
    if oldest_port in active_servers: del active_servers[oldest_port]
    time.sleep(2)

def ensure_server(port: int):
    with vram_lock:
        if is_listening(port):
            active_servers[port] = time.time()
            return True
        if port not in SERVER_COMMANDS: return False
        
        required = MODEL_VRAM_MAP.get(port, 20)
        current_total = sum(MODEL_VRAM_MAP.get(p, 20) for p in active_servers.keys() if is_listening(p))
        
        while current_total + required > VRAM_LIMIT:
            purge_oldest_server()
            current_total = sum(MODEL_VRAM_MAP.get(p, 20) for p in active_servers.keys() if is_listening(p))

        logger.info(f"📡 正在拉起端口 {port}，预估显存 {required}GB (总计 {current_total + required}GB)...")
        script = f'tell application "Terminal" to tell (make new tab at window 1) to do script "{SERVER_COMMANDS[port]}"'
        subprocess.run(["osascript", "-e", script])
        
        start_time = time.time()
        while time.time() - start_time < 150:
            if is_listening(port):
                # 尝试 API 握手 (Ollama 的路径不同)
                check_url = f"http://127.0.0.1:{port}/" if port == 11434 else f"http://127.0.0.1:{port}/v1/models"
                try:
                    with httpx.Client() as client:
                        if client.get(check_url, timeout=2).status_code in [200, 404]: # 404 for ollama root is fine
                            active_servers[port] = time.time()
                            logger.info(f"✅ 后端 {port} 就绪")
                            return True
                except: pass
            time.sleep(5)
        return False

async def openai_to_anthropic_stream(openai_response, model_name):
    msg_id = f"msg_{uuid.uuid4().hex}"
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': model_name, 'content': [], 'stop_reason': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
    async for line in openai_response.aiter_lines():
        if not line.startswith("data: ") or "[DONE]" in line: continue
        try:
            chunk = json.loads(line[6:])
            content = chunk['choices'][0].get('delta', {}).get('content', '')
            if content: yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': content}})}\n\n"
        except: continue
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def unified_proxy(request: Request, path: str):
    body = await request.body()
    try: data = json.loads(body) if body else {}
    except: data = {}
    
    model_name = data.get("model", "mtplx-qwen36-27b")
    target_port = MODEL_MAP.get(model_name, 8080)
    is_stream = data.get("stream", False)
    is_anthropic = "messages" in path

    if not ensure_server(target_port): raise HTTPException(status_code=504, detail="Backend Timeout")
    active_servers[target_port] = time.time()

    # 协议适配
    if is_anthropic:
        openai_messages = []
        if "system" in data: openai_messages.append({"role": "system", "content": data["system"]})
        for msg in data.get("messages", []):
            content = msg["content"]
            if isinstance(content, list): content = content[0].get("text", "")
            openai_messages.append({"role": msg["role"], "content": content})
        
        # 修正模型映射名，适配 MTPLX
        fw_model = "Qwen3.6-27B-MTPLX-Optimized-Quality" if target_port == 8080 else model_name
        forward_payload = {"model": fw_model, "messages": openai_messages, "stream": is_stream, "temperature": data.get("temperature", 0.7)}
    else:
        forward_payload = data

    target_url = f"http://127.0.0.1:{target_port}/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            if is_stream:
                req = client.build_request("POST", target_url, json=forward_payload)
                resp = await client.send(req, stream=True)
                if is_anthropic: return StreamingResponse(openai_to_anthropic_stream(resp, model_name), media_type="text/event-stream")
                return StreamingResponse(resp.aiter_raw(), status_code=resp.status_code, headers=dict(resp.headers))
            else:
                resp = await client.post(target_url, json=forward_payload)
                result = resp.json()
                if is_anthropic:
                    answer = result['choices'][0]['message']['content']
                    return JSONResponse({"id": f"msg_{uuid.uuid4().hex}", "type": "message", "role": "assistant", "model": model_name, "content": [{"type": "text", "text": answer}], "stop_reason": "end_turn", "usage": {"input_tokens": 0, "output_tokens": 0}})
                return JSONResponse(result)
        except Exception as e:
            logger.error(f"❌ 代理转发失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="error")
