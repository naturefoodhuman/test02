# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 13:50:00 CST
"""peer_review.config - 统一配置加载与 Schema 定义

公开 API：
- load_all_configs(): 一次性加载所有配置并交叉验证
- load_models_config() / load_routing_plans_config() / load_expert_configs(): 分项加载
- get_project_root(): 获取项目根目录
- schemas: ExpertConfig, ModelConfig, PlanConfig, RoutingPlansConfig, PrivacyPolicyConfig 等
- ConfigurationError: 配置错误异常类
"""

from peer_review.config.loader import (
    ConfigurationError,
    get_project_root,
    load_all_configs,
    load_expert_configs,
    load_models_config,
    load_privacy_policy_config,
    load_routing_plans_config,
)
from peer_review.config.schemas import (
    AppConfig,
    ExpertConfig,
    ExecutionMode,
    ExpertRole,
    ModelConfig,
    ModelType,
    NodeConfig,
    PlanConfig,
    PrivacyPolicyConfig,
    PrivacyPolicyEndpoint,
    PrivacyPolicyField,
    ReviewDimension,
    ReviewerConfig,
    RoutingPlansConfig,
    ModelsRegistryConfig,
)

__all__ = [
    # 核心加载函数
    "load_all_configs",
    "load_models_config",
    "load_routing_plans_config",
    "load_expert_configs",
    "load_privacy_policy_config",
    "get_project_root",
    "ConfigurationError",
    # Schema 类
    "ExpertConfig",
    "ReviewerConfig",
    "ModelConfig",
    "NodeConfig",
    "PlanConfig",
    "RoutingPlansConfig",
    "ModelsRegistryConfig",
    "AppConfig",
    "PrivacyPolicyConfig",
    "PrivacyPolicyField",
    "PrivacyPolicyEndpoint",
    # 枚举
    "ExpertRole",
    "ReviewDimension",
    "ExecutionMode",
    "ModelType",
]

__version__ = "0.2.0"
