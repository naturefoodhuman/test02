# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/api/__init__.py —— 事件 API 层聚合导出。
# 依据：ARCHITECTURE_FINAL §15.2（Events 域）；TASK_BACKLOG APC-T010。
"""事件 API 层聚合导出（/api/v1/events 路由）。"""

from .routes import router

__all__ = ["router"]
