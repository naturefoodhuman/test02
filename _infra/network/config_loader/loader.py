# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-25 00:00:00

"""Network 配置加载器（FORGE Factory 增量）

复用现有 FORGE 配置加载模式（peer_review.config.loader）。
提供：
- load_network_config()
- NetworkConfig（来自 schemas）
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .schemas import NetworkConfig
from _infra.network.core.secrets import load_local_env_files


class NetworkConfigError(Exception):
    """网络配置错误（与 FORGE ConfigurationError 风格一致）"""
    pass


def load_yaml_file(path: Path) -> dict[str, Any]:
    """安全加载 YAML（复用 peer_review 风格）"""
    if not path.exists():
        raise NetworkConfigError(f"network 配置文件不存在: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise NetworkConfigError(f"network.yaml 根节点必须是映射类型: {path}")
        return data
    except yaml.YAMLError as e:
        raise NetworkConfigError(f"YAML 解析失败 {path}: {e}") from e


def load_network_config(
    project_root: Path | None = None,
    config_path: str = "config/network.yaml",
) -> NetworkConfig:
    """
    加载 network.yaml 配置。

    Args:
        project_root: 项目根目录（可选，自动探测）
        config_path: 相对路径

    Returns:
        NetworkConfig（已校验）
    """
    if project_root is None:
        # 复用 FORGE 根探测逻辑
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "config" / "models.yaml").exists():
                project_root = parent
                break
        else:
            project_root = current

    load_local_env_files(project_root)

    full_path = project_root / config_path
    data = load_yaml_file(full_path)

    try:
        return NetworkConfig(**data)
    except Exception as e:
        raise NetworkConfigError(
            f"network.yaml 校验失败: {full_path}\n{e}"
        ) from e


def get_network_config_path(project_root: Path | None = None) -> Path:
    """返回 network.yaml 的完整路径（用于健康检查等）"""
    if project_root is None:
        project_root = Path.cwd()
        for parent in [project_root] + list(project_root.parents):
            if (parent / "config" / "models.yaml").exists():
                project_root = parent
                break
    return project_root / "config" / "network.yaml"
