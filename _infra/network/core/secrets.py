# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:10:00 CST

"""
密钥管理（FORGE Network 增量）

职责：
- 启动时校验必需密钥存在
- 不把密钥值输出到日志
- 提供便捷获取函数

当前必需密钥（按 NETWORK_ENGINEERING_DESIGN.md）：
- PII_MAP_ENCRYPTION_KEY（用于 pii_map.db 加密）
- 可选：TAVILY_API_KEY（仅手动 fallback）
"""

from __future__ import annotations

import os
from typing import Optional

from ..exceptions import ConfigError


REQUIRED_SECRETS = [
    "PII_MAP_ENCRYPTION_KEY",
]


OPTIONAL_SECRETS = [
    "TAVILY_API_KEY",
]


class SecretNotFoundError(ConfigError):
    code = "SECRET_NOT_FOUND"


def _mask(value: str, show: int = 4) -> str:
    """掩码显示密钥（仅用于错误信息）"""
    if not value:
        return "<empty>"
    if len(value) <= show * 2:
        return "***"
    return f"{value[:show]}...{value[-show:]}"


def validate_secrets() -> None:
    """
    启动时校验必需密钥。
    缺失则抛出清晰异常（不包含密钥值）。
    """
    missing = []
    for key in REQUIRED_SECRETS:
        if not os.getenv(key):
            missing.append(key)

    if missing:
        raise SecretNotFoundError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please set them in .env or your environment."
        )


def get_secret(name: str, required: bool = True) -> Optional[str]:
    """
    获取密钥。

    Args:
        name: 环境变量名
        required: 是否必须

    Returns:
        密钥值或 None

    Raises:
        SecretNotFoundError: required=True 且缺失时
    """
    value = os.getenv(name)
    if required and not value:
        raise SecretNotFoundError(f"Required secret '{name}' is not set")
    return value


def get_pii_encryption_key() -> str:
    """获取 PII 映射数据库加密密钥（必须）"""
    key = get_secret("PII_MAP_ENCRYPTION_KEY", required=True)
    if len(key) < 16:
        raise SecretNotFoundError("PII_MAP_ENCRYPTION_KEY must be at least 16 characters")
    return key


def has_tavily_key() -> bool:
    """检查是否配置了 Tavily fallback"""
    return bool(get_secret("TAVILY_API_KEY", required=False))
