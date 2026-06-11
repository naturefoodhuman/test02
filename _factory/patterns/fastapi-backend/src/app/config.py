# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""配置管理：所有可变参数从环境变量读取，禁止硬编码（需求 8.6）。

为保证在未安装 pydantic-settings 的环境也能导入 core 逻辑，
本模块用轻量自实现读取 env，不强依赖第三方库。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """应用配置（不可变）。

    Attributes:
        app_name: 应用名。
        version: 版本号。
        port: 监听端口。
    """

    app_name: str = os.getenv("APP_NAME", "forge-fastapi-pattern")
    version: str = os.getenv("APP_VERSION", "0.1.0")
    port: int = int(os.getenv("APP_PORT", "8000"))


def get_settings() -> Settings:
    """返回配置实例（便于测试时替换）。"""
    return Settings()
