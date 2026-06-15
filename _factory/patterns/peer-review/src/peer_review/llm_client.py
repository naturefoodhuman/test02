# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 03:20:00 CST
"""Peer-Review LLM 客户端

优先走 LiteLLM 网关 (localhost:4000)；网关不可用时回退到本地 Ollama；
本地 Ollama 也不可用时返回降级提示，保证图结构可运行。

v1.1.0 新增：
- 节点级数据出境二次校验：调用 API 模型前根据 DataPrivacyGate 检查数据字段
- 流式输出支持：对外输出 content chunks（供 Rich Live Display 使用）
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from peer_review.config.schemas import ModelConfig
from peer_review.platform.data_privacy_gate import DataPrivacyGate, GateDecisionType


@dataclass
class LLMResponse:
    content: str
    model: str
    error: str | None = None
    blocked: bool = False


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


def _privacy_check(
    model_cfg: ModelConfig,
    data_fields: dict[str, Any] | None,
    endpoint: str | None,
    approved: bool | None,
) -> LLMResponse | None:
    """节点级数据出境二次校验

    如果 data_fields 和 endpoint 已提供，且目标为 API 端点，
    在调用前再次确认策略。返回 None 表示无需阻断。
    """
    if model_cfg.type.value != "api":
        return None
    if not data_fields or not endpoint:
        return None

    # 如果 CLI 已明确批准，跳过二次校验
    if approved is True:
        return None

    # 定位项目根目录下的隐私策略文件
    # 从 llm_client.py 文件位置向上查找项目根（包含 config/ 和 _factory/ 的目录）
    file_dir = Path(__file__).resolve().parent
    project_root = file_dir
    for _ in range(5):  # 足够向上找到项目根
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
    """统一调用入口

    Args:
        model_cfg: 模型配置 (来自 models.yaml)
        messages: OpenAI 格式的消息列表
        privacy_context: 可选，包含：
            - data_fields: dict[str, Any] 待出境数据字段
            - endpoint: str 目标端点名（如 chinese_api）
            - approved: bool CLI 是否已批准

    Returns:
        LLMResponse 包含内容或降级/阻断信息
    """
    # 节点级隐私二次校验（仅 API 模型）
    if privacy_context:
        blocked = _privacy_check(
            model_cfg,
            privacy_context.get("data_fields"),
            privacy_context.get("endpoint"),
            privacy_context.get("approved"),
        )
        if blocked:
            return blocked

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


def chat_stream(
    model_cfg: ModelConfig,
    messages: list[dict[str, str]],
) -> LLMResponse:
    """流式调用入口（返回完整响应，内部按 chunk 聚合）

    当前实现与 chat() 行为一致，保留接口供后续接入流式网关。
    """
    # 优先使用 LiteLLM 网关流式接口
    base_url = "http://localhost:4000/v1"
    api_key = "sk-forge-local-anytoken"
    body = json.dumps({"model": model_cfg.model_id, "messages": messages, "stream": True}).encode("utf-8")
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
        with urllib.request.urlopen(req, timeout=120) as r:
            content_parts = []
            for line in r:
                line = line.decode("utf-8").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta and delta["content"]:
                        content_parts.append(delta["content"])
                except Exception:
                    continue
            return LLMResponse(content="".join(content_parts), model=model_cfg.model_id)
    except Exception:
        # 流式失败回退到非流式
        return chat(model_cfg, messages)
