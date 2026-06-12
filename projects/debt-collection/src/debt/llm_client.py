# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 01:30:00 CST
"""LLM 客户端：走工厂 LiteLLM 网关（localhost:4000），策略推理用。

设计：标准库 urllib 调用 OpenAI 兼容接口（零三方依赖）。
沙箱/网关未启动 → 优雅降级：返回 None 让上层走"离线模板"，不报死。
真机：start-litellm.sh 起网关后即真实调用 GLM/本地。
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMConfig:
    base_url: str = "http://localhost:4000/v1"
    model: str = "cloud/glm-primary"     # 策略推理默认 GLM（ADR-002）
    api_key: str = "sk-forge-local-anytoken"
    timeout: int = 120


def available(cfg: LLMConfig | None = None) -> bool:
    """探测网关是否可用（快速 HEAD/GET /models）。"""
    cfg = cfg or LLMConfig()
    try:
        req = urllib.request.Request(
            cfg.base_url.rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {cfg.api_key}"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def chat(prompt: str, *, system: str = "", cfg: LLMConfig | None = None,
         stream_hint: bool = True) -> str | None:
    """调用网关做一次对话。失败/不可用返回 None（上层降级）。

    Args:
        prompt: 用户提示。
        system: 系统提示。
        cfg: 配置。
        stream_hint: 仅记录意图；这里用非流式聚合(GLM 经网关已验证可用)。

    Returns:
        模型回复文本；不可用时 None。
    """
    cfg = cfg or LLMConfig()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({"model": cfg.model, "messages": messages}).encode("utf-8")
    try:
        req = urllib.request.Request(
            cfg.base_url.rstrip("/") + "/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {cfg.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=cfg.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001
        return None
