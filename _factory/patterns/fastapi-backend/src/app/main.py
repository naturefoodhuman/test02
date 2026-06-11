# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""FastAPI 应用入口（HTTP 层，薄封装，调用 core 逻辑）。

统一日志：输出到控制台，异常记录完整堆栈（需求 8.4）。
"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from app.config import get_settings
from app.core import build_greeting, health_payload

# 统一日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("forge.fastapi.pattern")

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.version)


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查端点。"""
    return health_payload(settings.version)


@app.get("/greet")
def greet(name: str | None = None) -> dict[str, str]:
    """问候端点（示例资源）。"""
    return {"message": build_greeting(name)}
