# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-26 00:00:00
# 重构时间（北京时间）：2026-07-09 17:05:00
# 重构内容：方案C - Tool Calling 全面支持 (BackendAdapter + Agent Loop)
"""Peer-Review LLM 客户端：多后端适配架构 (BackendAdapter Pattern)

支持多种推理框架：
- Ollama: 本地标准 API
- MTPLX: 高性能优化接口 (OpenAI Compatible)
- LiteLLM: 统一商业 API 网关
- MLX-LM / Llama.cpp: 通过相应适配器接入

v2.0.0 更新 (方案C)：
- 引入 ToolCall 数据类，LLMResponse 扩展
- 所有后端 chat/chat_stream 支持 tools 参数
- LiteLLMBackend 流式 tool_calls 解析
- 新增 chat_with_agent() 入口 (Agent Loop)
- messages 类型从 dict[str,str] 放宽为 dict[str,Any]
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Type

import time
import subprocess
from peer_review.config.schemas import ModelConfig
from peer_review.platform.data_privacy_gate import DataPrivacyGate, GateDecisionType

# ── ToolCall 数据类 (新增) ──────────────────────────────────────
@dataclass
class ToolCall:
    """一次工具调用"""
    id: str                              # 调用 ID (后端生成)
    name: str                            # 工具名称
    arguments: dict[str, Any]            # 解析后的参数
    raw_arguments: str = ""              # 原始 JSON 字符串 (流式拼接用)

# ── LLMResponse (扩展) ─────────────────────────────────────────
@dataclass
class LLMResponse:
    content: str
    model: str
    tool_calls: list[ToolCall] | None = None    # 新增
    error: str | None = None
    blocked: bool = False
    usage: dict[str, int] | None = None          # 新增
    finish_reason: str = "stop"                  # 新增 ("stop"|"tool_calls"|"length")

# ── 服务器启动指令注册表 ────────────────────────────────────────
def _load_server_commands() -> dict[int, str]:
    try:
        import sys
        root = Path(__file__).resolve().parents[5]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from _infra.model_runtime import get_server_commands
        return get_server_commands()
    except Exception:
        return {
            8080: "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080 > /tmp/mtplx_8080.log 2>&1 &",
            8082: "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082 > /tmp/mtplx_8082.log 2>&1 &",
            8084: "nohup llama-server -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > /tmp/llama_8084.log 2>&1 &",
        }

SERVER_COMMANDS = _load_server_commands()

def _ensure_server_running(base_url: str):
    """按需加载：如果端口没响应，尝试拉起服务器"""
    import urllib.parse
    parsed = urllib.parse.urlparse(base_url)
    if not parsed.port:
        return
    if parsed.hostname not in ["localhost", "127.0.0.1", "0.0.0.0"]:
        return
    port = parsed.port
    if port not in SERVER_COMMANDS:
        return
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", port)) == 0:
            return
    print(f"📡 检测到端口 {port} 未启动，正在按需加载模型...")
    subprocess.Popen(SERVER_COMMANDS[port], shell=True, executable="/bin/bash")
    for _ in range(30):
        time.sleep(3)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) == 0:
                print(f"✅ 端口 {port} 已就绪")
                return
    print(f"⚠️ 端口 {port} 启动超时")


# ── LLMBackend 抽象基类 (扩展: tools 参数) ─────────────────────
class LLMBackend(ABC):
    """LLM 推理后端抽象基类"""

    @abstractmethod
    def chat(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        pass

    @abstractmethod
    def chat_stream(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        pass


# ── LiteLLMBackend (Tool Calling + 流式解析) ───────────────────
class LiteLLMBackend(LLMBackend):
    """LiteLLM 网关适配器 (OpenAI 兼容接口) - 流式 + Tool Calling"""

    def chat(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        import httpx

        base_url = model_cfg.base_url or "http://localhost:4000/v1"
        model_id = model_cfg.model_id

        if base_url.rstrip("/").endswith("/v1"):
            chat_url = f"{base_url.rstrip('/')}/chat/completions"
        else:
            chat_url = f"{base_url.rstrip('/')}/v1/chat/completions"

        payload: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "stream": True,
            "temperature": 0.6,
            "max_tokens": 4096,
            "top_p": 0.95,
        }

        # Tool Calling 参数
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        CHUNK_IDLE_TIMEOUT = 600.0
        TOTAL_HARD_LIMIT = 14400.0

        content_parts: list[str] = []
        tool_call_buffers: dict[int, dict[str, str]] = {}  # index → {id, name, args}
        start_time = time.time()
        last_chunk_time = start_time
        finish_reason = "stop"
        usage_data = None

        try:
            with httpx.Client(
                timeout=httpx.Timeout(connect=10.0, read=None, write=30.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=0),
            ) as client:
                with client.stream("POST", chat_url, json=payload) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        now = time.time()
                        if now - last_chunk_time > CHUNK_IDLE_TIMEOUT:
                            raise TimeoutError(f"无新 token 超过 {CHUNK_IDLE_TIMEOUT}s")
                        if now - start_time > TOTAL_HARD_LIMIT:
                            raise TimeoutError("总时长超限")

                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        fr = choice.get("finish_reason")
                        if fr:
                            finish_reason = fr

                        # 提取 usage (部分 provider 在最后一个 chunk 返回)
                        if "usage" in chunk:
                            usage_data = chunk["usage"]

                        last_chunk_time = now

                        # 1. 文本内容
                        content_delta = delta.get("content", "")
                        if content_delta:
                            content_parts.append(content_delta)

                        # 2. Tool Calls (流式累积)
                        tc_deltas = delta.get("tool_calls")
                        if tc_deltas:
                            for tc_delta in tc_deltas:
                                idx = tc_delta.get("index", 0)
                                if idx not in tool_call_buffers:
                                    tool_call_buffers[idx] = {
                                        "id": tc_delta.get("id", ""),
                                        "name": "",
                                        "args": "",
                                    }
                                buf = tool_call_buffers[idx]
                                if tc_delta.get("id"):
                                    buf["id"] = tc_delta["id"]
                                func = tc_delta.get("function", {})
                                buf["name"] += func.get("name", "")
                                buf["args"] += func.get("arguments", "")

            # 组装结果
            full_content = "".join(content_parts)

            # 解析 tool_calls
            tool_calls: list[ToolCall] | None = None
            if tool_call_buffers:
                tool_calls = []
                for idx in sorted(tool_call_buffers.keys()):
                    buf = tool_call_buffers[idx]
                    raw_args = buf["args"]
                    try:
                        parsed_args = json.loads(raw_args) if raw_args else {}
                    except json.JSONDecodeError:
                        parsed_args = {"_raw": raw_args}
                    tool_calls.append(ToolCall(
                        id=buf["id"],
                        name=buf["name"],
                        arguments=parsed_args,
                        raw_arguments=raw_args,
                    ))
                if finish_reason == "stop" and tool_calls:
                    finish_reason = "tool_calls"

            return LLMResponse(
                content=full_content,
                model=model_id,
                tool_calls=tool_calls,
                usage=usage_data,
                finish_reason=finish_reason,
            )

        except Exception as e:
            print(f"❌ 流式后端调用失败: {e}")
            return LLMResponse(
                content=f"错误: {str(e)}",
                model=model_id,
                error=str(e),
                blocked=True,
            )

    def chat_stream(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        return self.chat(model_cfg, messages, tools=tools)


# ── OllamaBackend (Tool Calling 支持) ──────────────────────────
class OllamaBackend(LLMBackend):
    """Ollama 本地 API 适配器"""

    def chat(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        try:
            import ollama
            kwargs: dict[str, Any] = {
                "model": model_cfg.model_id,
                "messages": [{"role": m["role"], "content": m.get("content", "")} for m in messages if m.get("role") != "tool"],
                "stream": False,
            }
            if tools:
                kwargs["tools"] = tools

            response = ollama.chat(**kwargs)
            msg = response["message"]
            content = msg.get("content", "")

            # 解析 tool_calls
            tool_calls: list[ToolCall] | None = None
            raw_tcs = msg.get("tool_calls")
            if raw_tcs:
                tool_calls = []
                for i, tc in enumerate(raw_tcs):
                    func = tc.get("function", {})
                    tool_calls.append(ToolCall(
                        id=tc.get("id", f"ollama_call_{i}"),
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {}),
                    ))

            return LLMResponse(
                content=content,
                model=model_cfg.model_id,
                tool_calls=tool_calls,
                finish_reason="tool_calls" if tool_calls else "stop",
            )
        except Exception as e:
            print(f"❌ Ollama 调用失败: {e}")
            return None

    def chat_stream(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        return self.chat(model_cfg, messages, tools=tools)


# ── MTPLXBackend (Tool Calling 支持) ───────────────────────────
class MTPLXBackend(LLMBackend):
    """MTPLX 高性能适配器 (OpenAI Compatible)"""

    def chat(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        base_url = model_cfg.base_url or "http://localhost:8080/v1"
        _ensure_server_running(base_url)
        api_key = "mtplx-token"

        payload: dict[str, Any] = {
            "model": model_cfg.model_id,
            "messages": messages,
            "temperature": model_cfg.temperature if model_cfg.temperature is not None else 0.1,
            "top_p": model_cfg.top_p if model_cfg.top_p is not None else 1.0,
            "stream": False,
        }
        if model_cfg.max_tokens:
            payload["max_tokens"] = model_cfg.max_tokens

        # Tool Calling
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content", "") or ""
                finish_reason = choice.get("finish_reason", "stop")

                # 解析 tool_calls
                tool_calls: list[ToolCall] | None = None
                raw_tcs = message.get("tool_calls")
                if raw_tcs:
                    tool_calls = []
                    for tc in raw_tcs:
                        func = tc.get("function", {})
                        raw_args = func.get("arguments", "{}")
                        try:
                            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        except json.JSONDecodeError:
                            parsed_args = {"_raw": raw_args}
                        tool_calls.append(ToolCall(
                            id=tc.get("id", ""),
                            name=func.get("name", ""),
                            arguments=parsed_args,
                            raw_arguments=raw_args if isinstance(raw_args, str) else json.dumps(raw_args),
                        ))
                    if finish_reason == "stop":
                        finish_reason = "tool_calls"

                usage = data.get("usage")
                return LLMResponse(
                    content=content,
                    model=model_cfg.model_id,
                    tool_calls=tool_calls,
                    usage=usage,
                    finish_reason=finish_reason,
                )
        except Exception as e:
            print(f"❌ MTPLX 调用失败: {e}")
            return None

    def chat_stream(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        return self.chat(model_cfg, messages, tools=tools)


# ── LlamaCppBackend (Tool Calling 支持) ────────────────────────
class LlamaCppBackend(LLMBackend):
    """Llama.cpp Server 适配器"""

    def chat(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        base_url = model_cfg.base_url or "http://localhost:8081/v1"
        _ensure_server_running(base_url)

        payload: dict[str, Any] = {
            "model": model_cfg.model_id,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/chat/completions",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content", "") or ""
                finish_reason = choice.get("finish_reason", "stop")

                tool_calls: list[ToolCall] | None = None
                raw_tcs = message.get("tool_calls")
                if raw_tcs:
                    tool_calls = []
                    for tc in raw_tcs:
                        func = tc.get("function", {})
                        raw_args = func.get("arguments", "{}")
                        try:
                            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        except json.JSONDecodeError:
                            parsed_args = {"_raw": raw_args}
                        tool_calls.append(ToolCall(
                            id=tc.get("id", ""),
                            name=func.get("name", ""),
                            arguments=parsed_args,
                            raw_arguments=raw_args if isinstance(raw_args, str) else json.dumps(raw_args),
                        ))
                    if finish_reason == "stop":
                        finish_reason = "tool_calls"

                usage = data.get("usage")
                return LLMResponse(
                    content=content,
                    model=model_cfg.model_id,
                    tool_calls=tool_calls,
                    usage=usage,
                    finish_reason=finish_reason,
                )
        except Exception as e:
            print(f"❌ Llama.cpp 调用失败: {e}")
            return None

    def chat_stream(
        self,
        model_cfg: ModelConfig,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | None:
        return self.chat(model_cfg, messages, tools=tools)


# ── BackendFactory ──────────────────────────────────────────────
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


# ── 隐私校验 ──────────────────────────────────────────────────
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


# ── 统一调用入口 (扩展: tools 参数) ───────────────────────────
def chat(
    model_cfg: ModelConfig,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
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
    resp = backend.chat(model_cfg, messages, tools=tools)
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
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
) -> LLMResponse:
    """流式调用入口"""
    backend_name = getattr(model_cfg, "backend", "litellm")
    backend = BackendFactory.get_backend(backend_name)
    resp = backend.chat_stream(model_cfg, messages, tools=tools)
    if resp is not None:
        return resp
    return chat(model_cfg, messages, tools=tools)


# ── Agent Loop 入口 (新增) ─────────────────────────────────────
def chat_with_agent(
    model_cfg: ModelConfig,
    messages: list[dict[str, Any]],
    *,
    tool_registry: "ToolRegistry | None" = None,
    max_turns: int | None = None,
    privacy_context: dict[str, Any] | None = None,
    on_tool_call: Callable[[ToolCall], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
) -> LLMResponse:
    """带 Agent Loop 的调用入口，自动执行工具调用

    Args:
        model_cfg: 模型配置
        messages: 对话消息列表
        tool_registry: 工具注册表实例
        max_turns: 最大循环轮次 (默认取 model_cfg.max_agent_turns 或 10)
        privacy_context: 隐私校验上下文
        on_tool_call: 工具调用前回调
        on_tool_result: 工具结果回调 (name, result_str)
    """
    from peer_review.agent_loop import run_agent_loop
    from peer_review.tools.registry import ToolRegistry

    if tool_registry is None:
        tool_registry = ToolRegistry()

    if max_turns is None:
        max_turns = getattr(model_cfg, "max_agent_turns", 10) or 10

    return run_agent_loop(
        model_cfg=model_cfg,
        messages=messages,
        tool_registry=tool_registry,
        max_turns=max_turns,
        privacy_context=privacy_context,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
    )