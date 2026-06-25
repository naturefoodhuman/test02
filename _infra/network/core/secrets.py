# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
密钥管理（FORGE Network 增量）

职责：
- 启动时校验必需密钥存在
- 从本地 .env 文件加载可选密钥（不会覆盖已存在环境变量）
- 不把密钥值输出到日志
- 提供便捷获取函数

本地密钥文件（均应保持 gitignored）：
- <project_root>/.env
- <project_root>/_infra/.env
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ..exceptions import ConfigError

REQUIRED_SECRETS = [
    "PII_MAP_ENCRYPTION_KEY",
]

OPTIONAL_SECRETS = [
    "TAVILY_API_KEY",
    "SERPER_API_KEY",
    "BRAVE_API_KEY",
    "NETWORK_SEARCH_API_PROXY",
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


def _detect_project_root(start: Path | None = None) -> Path:
    current = start or Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "config" / "models.yaml").exists():
            return parent
    return current


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def load_local_env_files(project_root: Path | None = None) -> list[Path]:
    """
    Load local .env files without overriding already-exported variables.

    This avoids requiring python-dotenv and keeps the module local-first. The
    returned list contains files that existed and were parsed.
    """
    root = project_root or _detect_project_root()
    candidates = [root / ".env", root / "_infra" / ".env"]
    loaded: list[Path] = []
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                parsed = _parse_env_line(line)
                if not parsed:
                    continue
                key, value = parsed
                os.environ.setdefault(key, value)
            loaded.append(path)
        except OSError:
            continue
    return loaded


def validate_secrets() -> None:
    """
    启动时校验必需密钥。
    缺失则抛出清晰异常（不包含密钥值）。
    """
    load_local_env_files()
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
    load_local_env_files()
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


def has_serper_key() -> bool:
    """检查是否配置了 Serper fallback"""
    return bool(get_secret("SERPER_API_KEY", required=False))


def has_brave_key() -> bool:
    """检查是否配置了 Brave Search API fallback"""
    return bool(get_secret("BRAVE_API_KEY", required=False))
