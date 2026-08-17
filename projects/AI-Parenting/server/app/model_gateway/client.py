# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/model_gateway/client.py —— ModelClient 实现（APC-T024）。
# 依据：ENGINEERING_DESIGN §5.8（ModelClient Protocol）、§8；
#       ARCHITECTURE_FINAL §11.8（单一入口 Smart Proxy 4000，禁止绕过）；
#       TASK_BACKLOG APC-T024（chat/vision；文本 30s/视觉 60s；测试 FakeModelClient；CI 禁调真实模型）。
# 设计：SmartProxyModelClient —— HTTP POST 到 gateway_base_url/v1/messages（Anthropic 兼容），
#       按 plan 解析 model/max_tokens/temperature；chat 30s / vision 60s。
#       FakeModelClient —— 测试用，返回固定响应，不联网。
# 边界：本模块是项目内唯一 LLM/VLM 入口；Orchestrator/Copilot 只注入 ModelClient。

"""ModelClient 实现（APC-T024）。

- ``SmartProxyModelClient``：HTTP POST 到工厂 Smart Proxy（``gateway_base_url/v1/messages``，
  Anthropic Messages API 兼容）。按 ``plan`` 从 ``routing_plans`` 取 ``RoutingPlan``，
  组装请求体（``model``/``max_tokens``/``temperature``/``messages``）。``chat`` 超时 30s，
  ``vision`` 超时 60s（``is_vision`` plan 或图像路径）。网络错误/超时 → 抛 ``ModelError``，
  调用方处理（不静默吞错）。
- ``FakeModelClient``：测试用，返回固定 ``ModelResponse``，不联网。CI 默认用它（§0.5 安全）。
"""

from __future__ import annotations

from typing import Any

import httpx

from .domain import ModelResponse, RoutingPlan
from .routing import get_plan

# 超时（秒，PRD/TASK_BACKLOG APC-T024：文本 30s，视觉 60s）。
CHAT_TIMEOUT = 30.0
VISION_TIMEOUT = 60.0


class ModelError(RuntimeError):
    """模型调用失败（网络/超时/非 2xx）。"""


class SmartProxyModelClient:
    """工厂 Smart Proxy 薄客户端（APC-T024，项目内唯一 LLM/VLM 入口）。

    单一入口 ``gateway_base_url/v1/messages``（Anthropic Messages API 兼容）。
    按需注入 ``httpx.AsyncClient``（测试可注入 mock）；生产用模块级单例。
    """

    def __init__(
        self,
        base_url: str,
        plans: dict[str, RoutingPlan],
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._plans = plans
        # 测试可注入 mock client；生产懒创建（避免启动期开连接）。
        self._client = client
        self._owns_client = client is None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=VISION_TIMEOUT)
            self._owns_client = True
        return self._client

    async def aclose(self) -> None:
        """关闭内部 httpx client（若 owns）。"""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        plan: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        """文本对话（超时 30s）。按 plan 取 RoutingPlan，POST /v1/messages。"""
        rp = get_plan(self._plans, plan)
        if rp.is_vision:
            # chat 不应走 vision plan；防御性报错。
            raise ModelError(f"plan {plan} is vision-only, use vision() instead")
        body = _build_body(rp, messages, tools=tools)
        return await self._post(rp, body, timeout=CHAT_TIMEOUT)

    async def vision(self, plan: str, image: bytes, prompt: str) -> ModelResponse:
        """视觉理解（超时 60s）。image 为原始字节，按 base64 内嵌。"""
        rp = get_plan(self._plans, plan)
        import base64

        b64 = base64.b64encode(image).decode("ascii")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        body = _build_body(rp, messages, tools=None)
        return await self._post(rp, body, timeout=VISION_TIMEOUT)

    async def _post(self, rp: RoutingPlan, body: dict[str, Any], timeout: float) -> ModelResponse:
        """POST /v1/messages → ModelResponse；网络/超时/非 2xx → ModelError。"""
        client = self._get_client()
        try:
            resp = await client.post("/v1/messages", json=body, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise ModelError(f"model request timeout (plan={rp.key}, timeout={timeout}s)") from exc
        except httpx.HTTPError as exc:
            raise ModelError(f"model request error (plan={rp.key}): {exc}") from exc
        if resp.status_code >= 400:
            raise ModelError(
                f"model request failed (plan={rp.key}, status={resp.status_code}): {resp.text[:200]}"
            )
        return _parse_response(resp.json(), rp)


def _build_body(
    rp: RoutingPlan, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None
) -> dict[str, Any]:
    """组装 Anthropic Messages API 请求体。"""
    body: dict[str, Any] = {
        "model": rp.model,
        "max_tokens": rp.max_tokens,
        "temperature": rp.temperature,
        "messages": messages,
    }
    if tools:
        body["tools"] = tools
    return body


def _parse_response(data: dict[str, Any], rp: RoutingPlan) -> ModelResponse:
    """解析 Anthropic Messages 响应 → ModelResponse。"""
    # content 通常是 list[{"type":"text","text":"..."}]，拼接文本。
    content_blocks = data.get("content") or []
    if isinstance(content_blocks, list):
        text = "".join(
            b.get("text", "")
            for b in content_blocks
            if isinstance(b, dict) and b.get("type") == "text"
        )
    else:
        text = str(content_blocks)
    usage_raw = data.get("usage") or {}
    usage: dict[str, int] = {}
    if isinstance(usage_raw, dict):
        for k in ("input_tokens", "output_tokens"):
            v = usage_raw.get(k)
            if isinstance(v, int):
                usage[k] = v
    return ModelResponse(
        content=text,
        model=str(data.get("model", rp.model)),
        plan=rp.key,
        usage=usage,
        raw=data,
    )


class FakeModelClient:
    """测试用 ModelClient（APC-T024）：返回固定响应，不联网。

    CI 默认用它（§0.5 安全：禁调真实模型）。``responses`` 可预设按 plan 的响应；
    未预设时返回 plan key 的占位文本。记录调用历史供断言。
    """

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []  # (method, plan, kwargs)

    async def chat(
        self,
        plan: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        self.calls.append(("chat", plan, {"messages": messages, "tools": tools}))
        content = self._responses.get(plan, f"[fake:{plan}] chat response")
        return ModelResponse(
            content=content, model="fake-model", plan=plan, usage={"output_tokens": 1}
        )

    async def vision(self, plan: str, image: bytes, prompt: str) -> ModelResponse:
        self.calls.append(("vision", plan, {"prompt": prompt, "image_bytes": len(image)}))
        content = self._responses.get(plan, f"[fake:{plan}] vision response")
        return ModelResponse(
            content=content, model="fake-model", plan=plan, usage={"output_tokens": 1}
        )


__all__ = [
    "CHAT_TIMEOUT",
    "VISION_TIMEOUT",
    "FakeModelClient",
    "ModelError",
    "ModelResponse",
    "SmartProxyModelClient",
]
