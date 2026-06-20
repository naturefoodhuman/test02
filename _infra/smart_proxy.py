# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 13:30:00

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

FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import SERVER_COMMANDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE Real-time Stream Translator")

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
    script = f'tell application "Terminal" to tell (make new tab at window 1) to do script "{SERVER_COMMANDS[port]}"'
    subprocess.run(["osascript", "-e", script])
    start_time = time.time()
    while time.time() - start_time < 120:
        if is_listening(port):
            try:
                with httpx.Client() as client:
                    if client.get(f"http://127.0.0.1:{port}/v1/models", timeout=2).status_code == 200:
                        logger.info(f"✅ 后端 {port} 就绪")
                        return True
            except: pass
        time.sleep(4)
    return False

async def openai_to_anthropic_stream(openai_response, model_name):
    """【核心】将 OpenAI 的流式输出实时翻译成 Anthropic SSE 格式"""
    msg_id = f"msg_{uuid.uuid4().hex}"
    # 1. 发送 message_start
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': model_name, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
    # 2. 发送 content_block_start
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

    async for line in openai_response.aiter_lines():
        if not line or not line.startswith("data: "): continue
        if "[DONE]" in line: break
        
        try:
            chunk = json.loads(line[6:])
            delta = chunk['choices'][0].get('delta', {})
            content = delta.get('content', '')
            if content:
                # 3. 发送 content_block_delta
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': content}})}\n\n"
        except: continue

    # 4. 发送收尾事件
    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def protocol_translator(request: Request, path: str):
    body = await request.body()
    is_anthropic = "messages" in path
    
    try:
        data = json.loads(body)
        model_name = data.get("model", "")
        target_port = MODEL_MAP.get(model_name, 8080)
        is_stream = data.get("stream", False)
    except:
        return JSONResponse({"status": "alive"})

    if not is_listening(target_port):
        if not start_backend(target_port): raise HTTPException(status_code=504, detail="Backend Startup Timeout")

    # 协议转换
    if is_anthropic:
        logger.info(f"🔄 流式转换请求: {model_name} (Stream={is_stream})")
        openai_messages = []
        if "system" in data: openai_messages.append({"role": "system", "content": data["system"]})
        for msg in data.get("messages", []):
            content = msg["content"]
            if isinstance(content, list): content = content[0].get("text", "")
            openai_messages.append({"role": msg["role"], "content": content})
        
        forward_payload = {
            "model": "Qwen3.6-27B-MTPLX-Optimized-Quality",
            "messages": openai_messages,
            "stream": is_stream,
            "temperature": data.get("temperature", 0.7)
        }
    else:
        forward_payload = data

    target_url = f"http://127.0.0.1:{target_port}/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        if is_stream and is_anthropic:
            # 启用流式翻译
            req = client.build_request("POST", target_url, json=forward_payload)
            resp = await client.send(req, stream=True)
            return StreamingResponse(openai_to_anthropic_stream(resp, model_name), media_type="text/event-stream")
        else:
            # 常规请求
            resp = await client.post(target_url, json=forward_payload)
            result = resp.json()
            if is_anthropic:
                answer = result['choices'][0]['message']['content']
                return JSONResponse({
                    "id": f"msg_{uuid.uuid4().hex}", "type": "message", "role": "assistant",
                    "model": model_name, "content": [{"type": "text", "text": answer}],
                    "stop_reason": "end_turn", "usage": {"input_tokens": 0, "output_tokens": 0}
                })
            return JSONResponse(result)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="error")
