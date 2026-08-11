# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/service/__init__.py —— 事件用例服务层聚合导出。
# 依据：ENGINEERING_DESIGN §5.2（事务边界在 service）、§7.1（NOTIFY events.changed）、
#       §10.4（Audit 不可绕过）、§11（at-least-once）；TASK_BACKLOG APC-T009/T011。
"""事件用例服务层聚合导出（幂等写入 + 纠错 + 软删除 + 事件 worker）。"""

from .event_worker import EventWorker
from .idempotency import EventService

__all__ = ["EventService", "EventWorker"]
