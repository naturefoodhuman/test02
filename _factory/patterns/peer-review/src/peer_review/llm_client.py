# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:10:00 CST
"""Peer-Review LLM 客户端

优先走 LiteLLM 网关 (localhost:4000)；网关不可用时回退到本地 Ollama；
本地 Ollama 也不可用时返回降级提示，保证图结构可运行。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from peer_review.config.schemas import ModelConfig


@dataclass
class LLMResponse:
    content: str
    model: str
    error: str | None = None


def _call_litellm_gateway(
    model_name: str, messages: list[dict[str, str]], timeout: int = 120
) -> LLMResponse | None:
    """尝试调用 LiteLLM 网关（OpenAI 兼容接口）"""
    base_url = "http://localhost:4000/v1"
    api_key = "sk-forge-local-anytoken"
    body = json.dumps({"model": model_name, "messages": messages}).encode("utf-8")
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
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return LLMResponse(content=content, model=model_name)
    except Exception:
        return None


def _call_ollama_direct(model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse | None:
    """直接调用 Ollama 本地 API（网关不可用时回退）"""
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


def chat(model_cfg: ModelConfig, messages: list[dict[str, str]]) -> LLMResponse:
    """统一调用入口

    Args:
        model_cfg: 模型配置 (来自 models.yaml)
        messages: OpenAI 格式的消息列表

    Returns:
        LLMResponse 包含内容或降级错误信息
    """
    # 优先使用 LiteLLM 网关
    gateway_name = f"{model_cfg.type.value}/{model_cfg.model_id.replace(':', '/')}"
    if model_cfg.type.value == "api":
        gateway_name = f"api/{model_cfg.model_id}"

    resp = _call_litellm_gateway(gateway_name, messages)
    if resp is not None:
        return resp

    # 网关不可用：本地模型回退到 Ollama 直连
    if model_cfg.type.value == "local":
        resp = _call_ollama_direct(model_cfg, messages)
        if resp is not None:
            return resp

    # 完全不可用：返回降级信息
    return LLMResponse(
        content="[模型调用不可用：LiteLLM 网关未启动且 Ollama 不可达]",
        model=model_cfg.model_id,
        error="Gateway and Ollama both unavailable",
    )
