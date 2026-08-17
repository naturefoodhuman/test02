# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/model_gateway/domain.py —— Model Gateway 领域模型（APC-T024）。
# 依据：ENGINEERING_DESIGN §5.8（ModelClient Protocol：chat/vision）、§8（routing plan）；
#       ARCHITECTURE_FINAL §11.8（ModelClient 复用工厂 Smart Proxy 4000，单一入口）；
#       TASK_BACKLOG APC-T024（禁止任何模块直连云模型；chat/vision；文本 30s/视觉 60s；
#       测试默认 FakeModelClient，CI 禁调真实模型）。
# 设计：ModelClient Protocol（chat(plan, messages, tools) + vision(plan, image, prompt)）+
#       ModelResponse（content/usage/model/plan）+ RoutingPlan（model/max_tokens/temperature/is_vision）。
# 边界：本模块是项目内唯一 LLM/VLM 入口（架构 §11.8），Orchestrator/Copilot 只注入 ModelClient。

"""Model Gateway 领域模型（APC-T024）。

- ``ModelClient`` Protocol：项目内唯一 LLM/VLM 入口（架构 §11.8）。
  ``chat(plan, messages, tools=None)`` 文本对话；``vision(plan, image, prompt)`` 视觉理解。
  ``plan`` 对应 ``config/routing_plans.yaml`` 的 key（如 ``copilot.triage``、``vision.jaundice``）。
- ``ModelResponse``：``content``（文本）+ ``usage``（token 计数）+ ``model`` + ``plan``。
- ``RoutingPlan``：``model`` + ``max_tokens`` + ``temperature`` + ``is_vision``，从 YAML 加载。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ModelResponse:
    """模型响应（chat/vision 共用）。

    ``content`` 为模型输出的文本；``usage`` 为 token 计数（input/output）；
    ``model`` 为实际服务模型名；``plan`` 为所用路由计划 key（审计追溯）。
    """

    content: str
    model: str
    plan: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class RoutingPlan:
    """路由计划（config/routing_plans.yaml 一条）。

    ``model`` 指向工厂根 ``config/models.yaml`` 的模型 key；
    ``is_vision`` 标记视觉 plan（vision 调用走图像路径，超时 60s）。
    """

    key: str
    model: str
    max_tokens: int = 1024
    temperature: float = 0.3
    is_vision: bool = False
    description: str = ""


@runtime_checkable
class ModelClient(Protocol):
    """项目内唯一 LLM/VLM 入口（架构 §11.8）。

    所有 Orchestrator/Copilot/Camera 只注入 ``ModelClient``，禁止直连云模型。
    """

    async def chat(
        self,
        plan: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelResponse:
        """文本对话（超时 30s）。"""
        ...

    async def vision(self, plan: str, image: bytes, prompt: str) -> ModelResponse:
        """视觉理解（超时 60s）。"""
        ...


__all__ = ["ModelClient", "ModelResponse", "RoutingPlan"]
