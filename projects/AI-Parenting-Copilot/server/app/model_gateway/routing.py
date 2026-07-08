# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 23:55:00


"""Routing plan loader for the project-level Model Gateway."""

from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from server.app.common.errors import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROUTING_CONFIG = PROJECT_ROOT / "config" / "routing_plans.yaml"


class RoutingPlan(BaseModel):
    """Single model routing plan.

    `allow_cloud_fallback=True` does not bypass Privacy Gateway; callers must run
    cloud-bound content through `server.app.privacy.adapter` first.
    """

    provider: str = "smart_proxy"
    base_url: str | None = None
    model: str
    endpoint: str = "/v1/messages"
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    allow_cloud_fallback: bool = False
    safety_profile: str = "local_first"


class RoutingConfig(BaseModel):
    """Project routing plan config."""

    default_plan: str
    plans: dict[str, RoutingPlan]

    def resolve(self, key: str | None) -> tuple[str, RoutingPlan]:
        """Resolve a plan key or raise a configuration error."""

        plan_key = key or self.default_plan
        plan = self.plans.get(plan_key)
        if plan is None:
            raise ConfigurationError(
                "Unknown model routing plan",
                evidence={"plan_key": plan_key, "available": sorted(self.plans)},
            )
        return plan_key, plan


def load_routing_config(path: Path | None = None) -> RoutingConfig:
    """Load routing plans from YAML."""

    config_path = path or DEFAULT_ROUTING_CONFIG
    if not config_path.exists():
        raise ConfigurationError(
            "Routing config file not found",
            evidence={"path": str(config_path)},
        )
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return RoutingConfig.model_validate(raw)
