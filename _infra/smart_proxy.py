# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-25 00:00:00

import sys
import os
import uvicorn
import json
import time
import subprocess
import socket
import logging
import uuid
import re
import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from threading import Lock

FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import SERVER_COMMANDS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger("SmartProxy")

app = FastAPI(title="FORGE Unified Smart Proxy v4.0")

# 1. 物理 ID 映射表（显示用 + MTPLX 实际模型 ID）
# 关键修复：MTPLX 需要使用它自己注册的短 ID，而不是长 display_name
REAL_ID_MAP = {
    8080: "mtplx-qwen36-27b-optimized-quality",      # ← MTPLX 实际接受的 ID
    8082: "mtplx-gemma4-optimized-quality",
    8084: "qwopus-35b-a3b-v1-mtp-gguf-8bit",
    11434: "deepseek-r1:32b"
}

# 2. 别名路由表
MODEL_TO_PORT = {
    "mtplx-qwen36-27b": 8080,
    "mtplx-gemma4": 8082,
    "qwopus-35b": 8084,
    "local-deepseek-r1": 11434,
    # Claude Code for VS Code model aliases: all route to the local MTPLX main brain.
    "claude-3-5-sonnet-20241022": 8080,
    "claude-3-5-sonnet-latest": 8080,
    "claude-3-7-sonnet-20250219": 8080,
    "claude-3-5-haiku-20241022": 8080,
    "claude-opus-4-8": 8080,
    "claude-opus-4-1": 8080,
    "claude-opus-4-1-20250805": 8080,
    "claude-opus-4-20250514": 8080,
    "claude-opus-4-0": 8080,
    "claude-sonnet-4-20250514": 8080,
    "claude-sonnet-4-5": 8080,
    "claude-sonnet-4-5-20250929": 8080,
    # Claude Code for VS Code 2026 UI labels:
    # Default/Opus: Opus 4.8 (1M context)
    # Sonnet: Sonnet 4.6 / Sonnet 4.6 (1M context)
    # Haiku: Haiku 4.5
    "claude-opus-4-8-1m": 8080,
    "claude-opus-4-8-1m-20260101": 8080,
    "claude-opus-4-8-20260101": 8080,
    "claude-sonnet-4-6": 8080,
    "claude-sonnet-4-6-1m": 8080,
    "claude-sonnet-4-6-20260101": 8080,
    "claude-sonnet-4-6-1m-20260101": 8080,
    "claude-haiku-4-5": 8080,
    "claude-haiku-4-5-20260101": 8080,
}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m|\[[0-9;]*m")


def normalize_model_name(model_name: str) -> str:
    """Strip terminal ANSI fragments and normalize Claude Code aliases."""
    cleaned = ANSI_RE.sub("", str(model_name or "")).strip()
    # If Claude Code introduces a new Claude alias, default it to the local main brain
    # rather than failing with a remote model access error.
    return cleaned


def _extract_anthropic_text(content) -> str:
    """Convert Anthropic content blocks to plain text for OpenAI-compatible backends."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content or "")


def _bounded_max_tokens(value, default: int = 1024, cap: int | None = None) -> int:
    """Bound Claude Code max_tokens so local models do not generate forever."""
    cap = cap or int(os.getenv("FORGE_CLAUDE_CODE_MAX_TOKENS", "1024"))
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(1, min(parsed, cap))


def _anthropic_sse(event: str, payload: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")

# 显存管理
VRAM_LIMIT = 48
MODEL_VRAM = {8080: 20, 8082: 16, 8084: 36, 11434: 20}
active_servers = {}
vram_lock = Lock()
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0),
    limits=httpx.Limits(max_keepalive_connections=5)
)

def is_listening(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def ensure_server(port: int):
    with vram_lock:
        if is_listening(port):
            active_servers[port] = time.time()
            return True
        if port not in SERVER_COMMANDS: return False
        
        # 显存回收
        current = sum(MODEL_VRAM.get(p, 20) for p in active_servers if is_listening(p))
        while current + MODEL_VRAM.get(port, 20) > VRAM_LIMIT:
            oldest = min([p for p in active_servers if is_listening(p)], key=lambda x: active_servers[x])
            logger.info(f"⚠️ 卸载离线模型释放显存 (Port {oldest})")
            subprocess.run(f"pkill -9 -f '.*{oldest}'", shell=True)
            del active_servers[oldest]
            current = sum(MODEL_VRAM.get(p, 20) for p in active_servers if is_listening(p))

        logger.info(f"🚀 拉起真机模型 (Port {port})...")
        script = f'tell application "Terminal" to do script "{SERVER_COMMANDS[port]}"'
        subprocess.run(["osascript", "-e", script])
        
        start_ts = time.time()
        while time.time() - start_ts < 120:
            if is_listening(port):
                try:
                    # 必须确认 API 握手成功
                    check_url = f"http://127.0.0.1:{port}/v1/models"
                    if port == 11434: check_url = "http://127.0.0.1:11434/"
                    with httpx.Client() as client:
                        if client.get(check_url, timeout=2).status_code in [200, 404]:
                            logger.info(f"✅ 后端 {port} 响应就绪")
                            active_servers[port] = time.time()
                            time.sleep(5) # 显存稳定缓冲
                            return True
                except: pass
            time.sleep(5)
        return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_gateway(request: Request, path: str):
    body = await request.body()
    try: data = json.loads(body) if body else {}
    except: data = {}
    
    model_name = normalize_model_name(data.get("model", ""))
    target_port = MODEL_TO_PORT.get(model_name, 8080 if model_name.startswith("claude-") else 8080)
    is_anthropic = "messages" in path

    if not ensure_server(target_port): raise HTTPException(status_code=504, detail="Backend Timeout")
    active_servers[target_port] = time.time()

    # 【关键修复】使用 MTPLX 实际注册的 model id（社区最佳实践）
    # 不要用 display_name，直接用启动时显示的短 ID
    real_model_id = REAL_ID_MAP.get(target_port, model_name)

    # 构造 forward_payload（保留原始请求结构，减少转换风险）
    if is_anthropic:
        logger.info(f"🔄 协议转换: Anthropic -> OpenAI (Target: {real_model_id})")
        msgs = []
        if "system" in data:
            msgs.append({"role": "system", "content": data["system"]})
        for m in data.get("messages", []):
            content = _extract_anthropic_text(m.get("content", ""))
            msgs.append({"role": m.get("role", "user"), "content": content})
        wants_stream = bool(data.get("stream", False))
        forward_payload = {
            "model": real_model_id,
            "messages": msgs,
            "temperature": data.get("temperature", 0.3),
            "top_p": data.get("top_p", 0.9),
            "stream": wants_stream,
            "max_tokens": _bounded_max_tokens(data.get("max_tokens", 1024)),
        }
    else:
        # OpenAI 格式：直接使用客户端传来的 model（或映射后的真实 ID）
        forward_payload = data.copy() if isinstance(data, dict) else {}
        forward_payload["model"] = real_model_id
        # 确保必要字段存在（MTPLX 严格模式）
        forward_payload.setdefault("temperature", 0.6)
        forward_payload.setdefault("top_p", 0.95)
        forward_payload.setdefault("stream", False)
        forward_payload["max_tokens"] = _bounded_max_tokens(forward_payload.get("max_tokens", 1024))

    # 执行转发（带重试）
    target_url = f"http://127.0.0.1:{target_port}/v1/chat/completions"

    # Claude Code for VS Code typically requests Anthropic streaming. Convert
    # OpenAI-compatible backend SSE chunks into Anthropic Messages SSE events so
    # the VS Code UI receives incremental tokens instead of waiting for a full
    # local-model completion.
    if is_anthropic and forward_payload.get("stream"):
        async def anthropic_event_stream():
            msg_id = f"msg_{uuid.uuid4().hex}"
            yield _anthropic_sse("message_start", {
                "type": "message_start",
                "message": {
                    "id": msg_id,
                    "type": "message",
                    "role": "assistant",
                    "model": model_name,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                },
            })
            yield _anthropic_sse("content_block_start", {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            })
            try:
                async with http_client.stream("POST", target_url, json=forward_payload) as resp:
                    if resp.status_code != 200:
                        err = (await resp.aread()).decode("utf-8", errors="ignore")
                        yield _anthropic_sse("error", {"type": "error", "error": {"type": "api_error", "message": err}})
                        return
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        raw = line[5:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            chunk = json.loads(raw)
                        except Exception:
                            continue
                        for choice in chunk.get("choices", []):
                            delta = choice.get("delta", {}) or {}
                            text = delta.get("content")
                            if text:
                                yield _anthropic_sse("content_block_delta", {
                                    "type": "content_block_delta",
                                    "index": 0,
                                    "delta": {"type": "text_delta", "text": text},
                                })
            except Exception as exc:
                yield _anthropic_sse("error", {"type": "error", "error": {"type": "api_error", "message": str(exc)}})
                return
            yield _anthropic_sse("content_block_stop", {"type": "content_block_stop", "index": 0})
            yield _anthropic_sse("message_delta", {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": 0},
            })
            yield _anthropic_sse("message_stop", {"type": "message_stop"})

        return StreamingResponse(
            anthropic_event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    last_exception = None
    
    for attempt in range(3):  # 最多重试 3 次
        try:
            resp = await http_client.post(target_url, json=forward_payload)
            if resp.status_code == 200:
                res_json = resp.json()
                
                if is_anthropic:
                    ans = res_json['choices'][0]['message']['content']
                    return JSONResponse({
                        "id": f"msg_{uuid.uuid4().hex}", 
                        "type": "message", 
                        "role": "assistant", 
                        "model": model_name, 
                        "content": [{"type": "text", "text": ans}], 
                        "stop_reason": "end_turn", 
                        "usage": {"input_tokens": 0, "output_tokens": 0}
                    })
                return JSONResponse(res_json)
            else:
                logger.warning(f"⚠️ 后端返回 {resp.status_code}，第 {attempt+1} 次尝试")
                last_exception = f"HTTP {resp.status_code}"
                
        except Exception as e:
            last_exception = str(e)
            logger.warning(f"⚠️ 第 {attempt+1} 次转发失败: {e}")
            if attempt < 2:
                await asyncio.sleep(2)  # 等待 2 秒后重试
    
    logger.error(f"❌ 转发最终失败（已重试3次）: {last_exception}")
    raise HTTPException(status_code=504, detail=f"Backend timeout after 3 attempts: {last_exception}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="error")
