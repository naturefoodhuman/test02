# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""Normalization 模块（APC-T013）。

消费 ``ObservationEvent``，按 source 路由到 form/voice parser，写 ``*_log`` 派生表，
推进 ``processing_status=normalized``（架构 §7.1）。
"""

from .service import LogWriter, NormalizationService

__all__ = ["LogWriter", "NormalizationService"]
