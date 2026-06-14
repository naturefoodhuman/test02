# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 13:30:00 CST
"""Pydantic 配置 Schema 定义

替代手写 YAML 解析器，提供严格的类型校验和清晰的错误信息。
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ModelType(str, Enum):
    """模型类型枚举"""

    LOCAL = "local"
    API = "api"
    EMBEDDING = "embedding"


class ExecutionMode(str, Enum):
    """执行模式枚举"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SEQUENTIAL_ISOLATED = "sequential_isolated"


class ExpertRole(str, Enum):
    """专家角色枚举"""

    PRIMARY = "primary"
    REVIEWER = "reviewer"


class ReviewDimension(str, Enum):
    """评审维度枚举"""

    RISK = "risk"
    COMPLIANCE = "compliance"
    EXECUTION_STRATEGY = "execution_strategy"
    FEASIBILITY = "feasibility"
    LEGAL_ACCURACY = "legal_accuracy"


class ModelConfig(BaseModel):
    """模型配置 (对应 models.yaml 中的单个模型条目)"""

    display_name: str = Field(..., description="显示名称")
    provider: Literal["ollama", "deepseek", "alibaba", "zhipu"] = Field(..., description="提供商")
    model_id: str = Field(..., description="模型 ID (Ollama tag 或 API model name)")
    base_url: str = Field(default="http://localhost:11434", description="API 基础 URL")
    api_key: str | None = Field(default=None, description="API Key (引用环境变量如 ${DEEPSEEK_API_KEY})")
    type: ModelType = Field(default=ModelType.LOCAL, description="模型类型")
    estimated_speed: str | None = Field(default=None, description="预估速度")
    memory_required_gb: int = Field(default=0, ge=0, description="所需显存/内存 (GB)")
    capabilities: list[str] = Field(default_factory=list, description="能力标签")
    note: str | None = Field(default=None, description="备注")
    data_policy: str | None = Field(default=None, description="数据策略要求")

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_env_var(cls, v: str | None) -> str | None:
        """解析环境变量引用 ${VAR_NAME}"""
        if v and isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            import os

            env_name = v[2:-1]
            return os.getenv(env_name)
        return v


class NodeConfig(BaseModel):
    """路由方案中的单节点配置 (对应 routing_plans.yaml 中的节点)"""

    model: str = Field(..., description="引用 models.yaml 中的模型名")
    role: str | None = Field(default=None, description="角色标签")
    execution: ExecutionMode = Field(default=ExecutionMode.SEQUENTIAL, description="执行模式")
    note: str | None = Field(default=None, description="备注")


class PlanConfig(BaseModel):
    """单个路由方案配置"""

    description: str = Field(..., description="方案描述")
    estimated_total_time: str = Field(default="", description="预估总耗时")
    estimated_cost: str = Field(default="", description="预估成本")
    notes: str | None = Field(default=None, description="补充说明")
    nodes: dict[str, NodeConfig] = Field(..., description="节点配置映射")
    enabled: bool = Field(default=True, description="是否启用")


class RoutingPlansConfig(BaseModel):
    """路由方案表完整配置 (对应 routing_plans.yaml)"""

    active_plan: str = Field(..., description="当前激活的方案 ID")
    plans: dict[str, PlanConfig] = Field(..., description="所有方案")

    @model_validator(mode="after")
    def validate_active_plan_exists(self) -> "RoutingPlansConfig":
        if self.active_plan not in self.plans:
            raise ValueError(f"active_plan '{self.active_plan}' 不在 plans 中")
        if not self.plans[self.active_plan].enabled:
            raise ValueError(f"active_plan '{self.active_plan}' 未启用 (enabled: false)")
        return self


class ExpertConfig(BaseModel):
    """专家配置 (对应 expert.yaml)"""

    id: str = Field(..., min_length=1, description="专家唯一标识，必填")
    name: str = Field(..., min_length=1, description="专家显示名称")
    role: ExpertRole = Field(..., description="角色: primary 或 reviewer")
    specialization: str | None = Field(default=None, description="专业领域标识")
    model: str = Field(default="qwen3.6:35b-a3b-q8_0", description="使用的模型名 (引用 models.yaml)")
    knowledge_sources: list[str] = Field(default_factory=list, description="知识源文件列表")
    review_dimensions: list[ReviewDimension] = Field(default_factory=list, description="评审维度")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="权重 (0-1)")
    system_prompt: str = Field(default="", description="系统提示词")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """ID 必须是合法标识符：小写字母、数字、连字符"""
        import re

        if not re.match(r"^[a-z][a-z0-9-]*$", v):
            raise ValueError(
                f"id 必须以小写字母开头，仅包含小写字母、数字、连字符: {v}"
            )
        return v

    @field_validator("review_dimensions", mode="before")
    @classmethod
    def parse_dimensions(cls, v: Any) -> list[ReviewDimension]:
        """支持字符串列表自动转枚举"""
        if isinstance(v, list):
            return [ReviewDimension(d) if isinstance(d, str) else d for d in v]
        return v

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v: Any) -> ExpertRole:
        """兼容字符串和嵌套结构"""
        if isinstance(v, dict):
            # 兼容旧版嵌套结构 {identity: "...", ...}
            return ExpertRole.PRIMARY
        return ExpertRole(v) if isinstance(v, str) else v


class ReviewerConfig(BaseModel):
    """评审员配置 (可选，用于更细粒度控制)"""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    model: str = Field(default="qwen3.6:35b-a3b-q8_0")
    dimensions: list[ReviewDimension] = Field(default_factory=list)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    execution: ExecutionMode = Field(default=ExecutionMode.SEQUENTIAL)
    system_prompt: str = Field(default="")

    @field_validator("dimensions", mode="before")
    @classmethod
    def parse_dimensions(cls, v: Any) -> list[ReviewDimension]:
        if isinstance(v, list):
            return [ReviewDimension(d) if isinstance(d, str) else d for d in v]
        return v


class PrivacyPolicyField(BaseModel):
    """隐私策略字段定义"""

    label: str = Field(..., description="字段中文标签")
    policy: Literal["local_only", "human_approve", "mask_then_allow", "allow"] = Field(
        ..., description="策略类型"
    )
    mask_rule: str | None = Field(default=None, description="脱敏规则名")
    note: str = Field(default="", description="备注")


class PrivacyPolicyEndpoint(BaseModel):
    """隐私策略目标端点"""

    display_name: str = Field(..., description="端点显示名称")
    allowed_policies: list[str] = Field(default_factory=list, description="允许的策略类型")
    requires_human_for: list[str] = Field(default_factory=list, description="需人工确认的策略")
    data_residency: str | None = Field(default=None, description="数据驻留地区")
    note: str | None = Field(default=None, description="备注")


class PrivacyPolicyConfig(BaseModel):
    """隐私策略完整配置 (对应 privacy_policy.yaml)"""

    version: str = Field(default="1.0", description="策略版本")
    project: str = Field(..., description="项目名")
    last_reviewed: str = Field(..., description="最后审核日期")
    reviewed_by: str = Field(..., description="审核人")
    fields: dict[str, PrivacyPolicyField] = Field(default_factory=dict, description="字段策略")
    endpoints: dict[str, PrivacyPolicyEndpoint] = Field(
        default_factory=dict, description="端点策略"
    )
    human_approval_triggers: list[dict[str, Any]] = Field(
        default_factory=list, description="人工审核触发规则"
    )
    masking_pipeline: dict[str, Any] = Field(default_factory=dict, description="脱敏管道配置")


# ──────────────────────────────────────────────────────────────────
# 统一配置容器（供 RoutingPlanEngine 使用）
# ──────────────────────────────────────────────────────────────────

class ModelsRegistryConfig(BaseModel):
    """models.yaml 完整结构"""

    models: dict[str, ModelConfig] = Field(..., description="模型注册表")


class AppConfig(BaseModel):
    """应用级聚合配置（运行时组装）"""

    models: ModelsRegistryConfig
    routing: RoutingPlansConfig
    privacy: PrivacyPolicyConfig | None = None
    experts: dict[str, ExpertConfig] = Field(default_factory=dict)

    def get_active_plan(self) -> PlanConfig:
        return self.routing.plans[self.routing.active_plan]

    def get_model_for_node(self, node_name: str) -> ModelConfig:
        plan = self.get_active_plan()
        if node_name not in plan.nodes:
            raise KeyError(f"方案中未定义节点: {node_name}")
        model_name = plan.nodes[node_name].model
        if model_name not in self.models.models:
            raise KeyError(f"models.yaml 中未定义模型: {model_name}")
        return self.models.models[model_name]