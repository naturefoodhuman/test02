# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/model_gateway/routing.py —— 路由计划加载器（APC-T024）。
# 依据：ENGINEERING_DESIGN §5.8、§8.2（config/routing_plans.yaml 项目专属路由）；
#       ARCHITECTURE_FINAL §11.8；TASK_BACKLOG APC-T024。
# 设计：load_plans(path) 读 YAML → dict[str, RoutingPlan]；get_plan(key) 取单条。
#       缺 plan key → KeyError（调用方处理，与 RuleRegistry 一致）。
# 边界：只解析路由计划，不调模型（调模型在 client.py）。

"""路由计划加载器（APC-T024）。

读 ``config/routing_plans.yaml`` → ``dict[str, RoutingPlan]``。``get_plan(key)`` 取单条，
缺 key 抛 ``KeyError``（调用方处理，与 ``RuleRegistry`` 一致）。

YAML 结构（项目专属，简化单节点）::

    plans:
      copilot.triage:
        model: mtplx-qwen36-27b
        max_tokens: 1024
        temperature: 0.3
        description: "分诊 Copilot"
      vision.jaundice:
        model: mtplx-qwen36-27b
        max_tokens: 512
        temperature: 0.2
        is_vision: true
        description: "黄疸照片视觉理解"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .domain import RoutingPlan


def load_plans(path: Path) -> dict[str, RoutingPlan]:
    """读 routing_plans.yaml → {plan_key: RoutingPlan}。

    缺文件或空 plans → 空 dict（调用方按需处理 KeyError）。
    """
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    plans: dict[str, RoutingPlan] = {}
    raw_plans = data.get("plans") or {}
    if not isinstance(raw_plans, dict):
        return {}
    for key, val in raw_plans.items():
        if not isinstance(val, dict):
            continue
        plans[str(key)] = _to_plan(str(key), val)
    return plans


def get_plan(plans: dict[str, RoutingPlan], key: str) -> RoutingPlan:
    """取单条 plan；缺 key 抛 KeyError。"""
    if key not in plans:
        raise KeyError(f"routing plan not found: {key}")
    return plans[key]


def _to_plan(key: str, val: dict[str, Any]) -> RoutingPlan:
    """dict → RoutingPlan（字段容错，缺省用默认）。"""
    temp = _as_float(val.get("temperature"))
    return RoutingPlan(
        key=key,
        model=str(val.get("model", "")),
        max_tokens=_as_int(val.get("max_tokens")) or 1024,
        temperature=temp if temp is not None else 0.3,
        is_vision=bool(val.get("is_vision", False)),
        description=str(val.get("description", "")),
    )


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


__all__ = ["get_plan", "load_plans"]
