# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""Normalization 模块（APC-T013 / APC-T014）。

消费 ``ObservationEvent``，按 source 路由到 form/voice parser，写 ``*_log`` 派生表，
推进 ``processing_status=normalized``（架构 §7.1）。APC-T014 增常驻 worker 订阅
``events.changed``，处理纠错链/软删除对派生表的影响。
"""

from .service import LogWriter, NormalizationService
from .worker import NormalizationWorker

__all__ = ["LogWriter", "NormalizationService", "NormalizationWorker"]
