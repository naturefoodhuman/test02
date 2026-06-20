# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 12:00:00 CST
"""Peer-Review LLM 客户端：多后端适配架构 (BackendAdapter Pattern)

支持多种推理框架：
- Ollama: 本地标准 API
- MTPLX: 高性能优化接口 (OpenAI Compatible)
- LiteLLM: 统一商业 API 网关
- MLX-LM / Llama.cpp: 通过相应适配器接入

v1.2.0 更新：
- 引入 LLMBackend 抽象基类
- 实现 BackendFactory 动态加载
- 支持 MTPLX 高速推理后端
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type

import time
import subprocess
from peer_review.config.schemas import ModelConfig
from peer_review.platform.data_privacy_gate import DataPrivacyGate, GateDecisionType

# ── 服务器启动指令注册表 (需求 1, 8, 11) ──────────────────────────
SERVER_COMMANDS = {
    8080: "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080 > /tmp/mtplx_8080.log 2>&1 &",
    8082: "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082 > /tmp/mtplx_8082.log 2>&1 &",
    8084: "nohup llama-server -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > /tmp/llama_8084.log 2>&1 &",
}

def _ensure_server_running(base_url: str):
    """按需加载：如果端口没响应，尝试拉起服务器 (R11)"""
    import urllib.parse
    parsed = urllib.parse.urlparse(base_url)
    if not parsed.port:
        return

    # 允许 hostname 为 localhost 或 0.0.0.0 或 127.0.0.1
    if parsed.hostname not in ["localhost", "127.0.0.1", "0.0.0.0"]:
        return

    port = parsed.port
    if port not in SERVER_COMMANDS:
        return

    # 检查端口
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", port)) == 0:
            return # 已运行

    print(f"📡 检测到端口 {port} 未启动，正在按需加载模型...")
    subprocess.Popen(SERVER_COMMANDS[port], shell=True, executable="/bin/bash")
    
    # 等待就绪 (冷启动可能需要一点时间)
    for _ in range(30):
        time.sleep(3)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) == 0:
                print(f"✅ 端口 {port} 已就绪")
                return
    print(f"⚠️ 端口 {port} 启动超时")

@dataclass
class LLMResponse:
    content: str
    model: str
    error: str | None = None
    blocked: bool = False


class LLMBackend(ABC):
    """LLM 推理后端抽象基类"""
    
    @abstractmethod
    def chat(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        pass

    @abstractmethod
    def chat_stream(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        pass


class LiteLLMBackend(LLMBackend):
    """LiteLLM 网关适配器 (OpenAI 兼容接口)"""
    
    def chat(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        # 使用 LiteLLM 的标准 OpenAI 兼容格式
        base_url = model_cfg.base_url or "http://localhost:4000/v1"
        api_key = model_cfg.api_key or "sk-forge-local-anytoken"
        
        # 处理 model_id 映射
        model_id = model_cfg.model_id
        if model_cfg.type.value == "api":
            # 确保 API 路由正确
            pass 
        
        body = json.dumps({"model": model_id, "messages": messages}).encode("utf-8")
        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return LLMResponse(content=content, model=model_id)
        except Exception as e:
            print(f"❌ 后端调用失败: {e}")
            return LLMResponse(content=f"错误: {str(e)}", model=model_id, error=str(e), blocked=True)

    def chat_stream(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        # 简化实现：先调用 chat() 聚合
        return self.chat(model_cfg, messages)


class OllamaBackend(LLMBackend):
    """Ollama 本地 API 适配器"""
    
    def chat(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        try:
            import ollama
            response = ollama.chat(
                model=model_cfg.model_id,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                stream=False,
            )
            return LLMResponse(content=response["message"]["content"], model=model_cfg.model_id)
        except Exception:
            return None

    def chat_stream(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        return self.chat(model_cfg, messages)


class MTPLXBackend(LLMBackend):
    """MTPLX 高性能适配器 (OpenAI Compatible)"""
    
    def chat(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        # MTPLX 通常提供高性能 OpenAI 兼容接口
        base_url = model_cfg.base_url or "http://localhost:8080/v1"
        _ensure_server_running(base_url)
        api_key = "mtplx-token"
        
        # 构建请求体，包含自定义参数 (需求 5)
        payload = {
            "model": model_cfg.model_id,
            "messages": messages,
            "temperature": model_cfg.temperature if model_cfg.temperature is not None else 0.1,
            "top_p": model_cfg.top_p if model_cfg.top_p is not None else 1.0,
            "stream": model_cfg.stream,
        }
        if model_cfg.max_tokens:
            payload["max_tokens"] = model_cfg.max_tokens

        body = json.dumps(payload).encode("utf-8")
        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return LLMResponse(content=content, model=model_cfg.model_id)
        except Exception:
            return None

    def chat_stream(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        return self.chat(model_cfg, messages)


class LlamaCppBackend(LLMBackend):
    """Llama.cpp Server 适配器"""
    
    def chat(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        base_url = model_cfg.base_url or "http://localhost:8081/v1"
        _ensure_server_running(base_url)
        body = json.dumps({"model": model_cfg.model_id, "messages": messages}).encode("utf-8")
        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/chat/completions",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return LLMResponse(content=content, model=model_cfg.model_id)
        except Exception:
            return None

    def chat_stream(self, model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
        return self.chat(model_cfg, messages)


class BackendFactory:
    """后端工厂：根据配置选择适配器"""
    _backends: dict[str, Type[LLMBackend]] = {
        "ollama": OllamaBackend,
        "mtplx": MTPLXBackend,
        "litellm": LiteLLMBackend,
        "llama_cpp": LlamaCppBackend,
    }

    @classmethod
    def get_backend(cls, backend_name: str | None) -> LLMBackend:
        backend_cls = cls._backends.get(backend_name, LiteLLMBackend)
        return backend_cls()


def _privacy_check(
    model_cfg: ModelConfig,
    data_fields: dict[str, Any] | None,
    endpoint: str | None,
    approved: bool | None,
) -> LLMResponse | None:
    """节点级数据出境二次校验"""
    if model_cfg.type.value != "api":
        return None
    if not data_fields or not endpoint:
        return None
    if approved is True:
        return None

    file_dir = Path(__file__).resolve().parent
    project_root = file_dir
    for _ in range(5):
        if (project_root / "config" / "privacy_policy.yaml").exists():
            break
        project_root = project_root.parent
    policy_path = project_root / "config" / "privacy_policy.yaml"
    gate = DataPrivacyGate(policy_path)
    result = gate.check(data_fields, endpoint)

    if result.blocked_fields:
        return LLMResponse(
            content="[节点级数据出境被阻断：字段违反 local_only 策略]",
            model=model_cfg.model_id,
            error=f"blocked_fields={result.blocked_fields}",
            blocked=True,
        )

    if result.requires_human_fields:
        return LLMResponse(
            content="[节点级数据出境需人工确认：请先在 CLI 完成 DataPrivacyGate 审核]",
            model=model_cfg.model_id,
            error=f"requires_human_fields={result.requires_human_fields}",
            blocked=True,
        )
    return None


def chat(
    model_cfg: ModelConfig,
    messages: list[dict[str, str]],
    *,
    privacy_context: dict[str, Any] | None = None,
) -> LLMResponse:
    """统一调用入口"""
    # 1. 隐私校验
    if privacy_context:
        blocked = _privacy_check(
            model_cfg,
            privacy_context.get("data_fields"),
            privacy_context.get("endpoint"),
            privacy_context.get("approved"),
        )
        if blocked:
            return blocked

    # 2. 选择后端
    backend_name = getattr(model_cfg, "backend", "litellm")
    backend = BackendFactory.get_backend(backend_name)
    
    # 3. 执行调用
    resp = backend.chat(model_cfg, messages)
    if resp is not None:
        return resp

    # 4. 最终降级
    return LLMResponse(
        content=f"[模型调用不可用：后端 {backend_name} 无法连接]",
        model=model_cfg.model_id,
        error="Backend connection failed",
    )


def chat_stream(
    model_cfg: ModelConfig,
    messages: list[dict[str, str]],
) -> LLMResponse:
    """流式调用入口"""
    backend_name = getattr(model_cfg, "backend", "litellm")
    backend = BackendFactory.get_backend(backend_name)
    resp = backend.chat_stream(model_cfg, messages)
    if resp is not None:
        return resp
    return chat(model_cfg, messages)
