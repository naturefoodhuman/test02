# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 13:45:00 CST
"""统一配置加载入口

替代手写的 _load_yaml_simple，使用 Pydantic 严格校验。
所有配置错误在启动时明确报错，不再静默失败。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from peer_review.config.schemas import (
    AppConfig,
    ExpertConfig,
    ModelsRegistryConfig,
    PrivacyPolicyConfig,
    RoutingPlansConfig,
)


class ConfigurationError(Exception):
    """配置错误：启动时抛出，明确提示修复方向"""

    pass


def load_yaml_file(path: Path) -> dict[str, Any]:
    """安全加载 YAML 文件"""
    if not path.exists():
        raise ConfigurationError(f"配置文件不存在: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ConfigurationError(f"YAML 根节点必须是映射类型: {path}")
        return data
    except yaml.YAMLError as e:
        raise ConfigurationError(f"YAML 解析失败 {path}: {e}") from e


def load_models_config(path: Path) -> ModelsRegistryConfig:
    """加载 models.yaml (A 文件)"""
    data = load_yaml_file(path)
    if "models" not in data:
        raise ConfigurationError(f"models.yaml 缺少顶层 'models' 键: {path}")
    try:
        return ModelsRegistryConfig(models=data["models"])
    except Exception as e:
        raise ConfigurationError(f"models.yaml 校验失败: {e}") from e


def load_routing_plans_config(path: Path) -> RoutingPlansConfig:
    """加载 routing_plans.yaml (B 文件)"""
    data = load_yaml_file(path)
    try:
        return RoutingPlansConfig(**data)
    except Exception as e:
        raise ConfigurationError(f"routing_plans.yaml 校验失败: {path}\n{e}") from e


def load_privacy_policy_config(path: Path) -> PrivacyPolicyConfig | None:
    """加载 privacy_policy.yaml (可选)"""
    if not path.exists():
        return None
    data = load_yaml_file(path)
    try:
        return PrivacyPolicyConfig(**data)
    except Exception as e:
        raise ConfigurationError(f"privacy_policy.yaml 校验失败: {path}\n{e}") from e


def load_expert_configs(experts_dir: Path) -> dict[str, ExpertConfig]:
    """加载所有专家配置 (扫描 *.expert/expert.yaml)"""
    experts: dict[str, ExpertConfig] = {}
    if not experts_dir.exists():
        raise ConfigurationError(f"专家目录不存在: {experts_dir}")

    for expert_dir in experts_dir.glob("*.expert"):
        # 跳过模板目录
        if expert_dir.name.startswith("_"):
            continue
        yaml_path = expert_dir / "expert.yaml"
        if not yaml_path.exists():
            continue
        data = load_yaml_file(yaml_path)
        if not data:
            continue

        # 兼容：目录名作为 fallback ID
        fallback_id = expert_dir.name.replace(".expert", "")
        data.setdefault("id", fallback_id)

        try:
            expert = ExpertConfig(**data)
            if expert.id in experts:
                raise ConfigurationError(f"重复的专家 ID: {expert.id}")
            experts[expert.id] = expert
        except Exception as e:
            raise ConfigurationError(f"专家配置校验失败 {yaml_path}: {e}") from e

    if not experts:
        raise ConfigurationError(f"未找到任何有效专家配置: {experts_dir}")

    # 必须有且仅有一个 primary
    primaries = [e for e in experts.values() if e.role.value == "primary"]
    if len(primaries) != 1:
        raise ConfigurationError(
            f"必须有且仅有一个 primary 专家，当前: {len(primaries)} 个"
        )

    return experts


def load_all_configs(
    project_root: Path,
    *,
    models_file: str = "config/models.yaml",
    plans_file: str = "config/routing_plans.yaml",
    privacy_file: str = "config/privacy_policy.yaml",
    experts_dir: str = "_factory/experts",
) -> AppConfig:
    """一次性加载所有配置，启动时交叉验证

    Args:
        project_root: 项目根目录 (包含 config/ 和 _factory/ 的父目录)
        models_file: 相对 project_root 的 models.yaml 路径
        plans_file: 相对 project_root 的 routing_plans.yaml 路径
        privacy_file: 相对 project_root 的 privacy_policy.yaml 路径
        experts_dir: 相对 project_root 的专家目录

    Returns:
        AppConfig: 聚合配置对象，已通过交叉验证

    Raises:
        ConfigurationError: 任何配置不一致或校验失败
    """
    # 加载三大核心配置
    models_cfg = load_models_config(project_root / models_file)
    routing_cfg = load_routing_plans_config(project_root / plans_file)
    privacy_cfg = load_privacy_policy_config(project_root / privacy_file)
    experts_cfg = load_expert_configs(project_root / experts_dir)

    # 交叉验证：B 文件引用的模型必须在 A 文件中定义
    available_models = set(models_cfg.models.keys())
    errors: list[str] = []

    for plan_id, plan in routing_cfg.plans.items():
        for node_name, node_cfg in plan.nodes.items():
            if node_cfg.model not in available_models:
                errors.append(
                    f"方案 '{plan_id}' 节点 '{node_name}' "
                    f"引用了未定义的模型 '{node_cfg.model}'"
                )

    # 验证专家引用的模型
    for expert_id, expert in experts_cfg.items():
        if expert.model not in available_models:
            errors.append(
                f"专家 '{expert_id}' 引用了未定义的模型 '{expert.model}'"
            )

    if errors:
        raise ConfigurationError("模型配置不一致：\n" + "\n".join(errors))

    return AppConfig(
        models=models_cfg,
        routing=routing_cfg,
        privacy=privacy_cfg,
        experts=experts_cfg,
    )


def get_project_root() -> Path:
    """获取项目根目录 (通过环境变量或向上查找)"""
    # 优先使用环境变量
    env_root = os.getenv("FORGE_PROJECT_ROOT")
    if env_root:
        return Path(env_root)

    # 向上查找包含 config/models.yaml 的目录
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "config" / "models.yaml").exists():
            return parent
        if (parent / "_factory" / "experts").exists():
            return parent

    # 兜底：当前工作目录
    return current