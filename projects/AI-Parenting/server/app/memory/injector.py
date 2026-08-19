# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-19 00:00:00
#
# app/memory/injector.py —— MemorySnapshot 聚合注入器（APC-T026）。
# 依据：ENGINEERING_DESIGN §5.9（Orchestrator 一次性获取 memory）；ARCHITECTURE_FINAL §4.3
#       （健康类回答前注入完整五层）；TASK_BACKLOG APC-T026（Orchestrator 可一次性获取
#       完整 CopilotContext 所需 memory）。
# 设计：MemoryInjector.build_snapshot(baby_id, family_id) 聚合 M1-M5 → MemorySnapshot。
#       各层失败隔离（单层异常不阻断整体，降级为 None/空，记日志），at-least-once 由调用方补偿。
# 边界：只读聚合，不产生告警等级、不做医疗判断。rule_version 占位 None（T019 接入后填充）。

"""MemorySnapshot 聚合注入器（APC-T026）。

``MemoryInjector.build_snapshot`` 一次性聚合 M1-M5 → ``MemorySnapshot``，供 Orchestrator
注入健康类回答上下文（架构 §4.3 / PRD §9）。各层失败隔离：单层异常降级为 None/空，
不阻断整体快照构建（at-least-once 由调用方后续补偿）。

``rule_version`` 占位 None（PRD §9 要求注入"相关规则版本"）；T019 EvidencePolicy
``get_current`` 接入后由 Orchestrator 填充（避免 T026 提前耦合 T019 仓储）。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .domain import MemorySnapshot

if TYPE_CHECKING:
    from .domain import MemoryStore

logger = logging.getLogger(__name__)


class MemoryInjector:
    """五层记忆聚合注入器（APC-T026）。

    构造注入 ``MemoryStore``（请求作用域）。``build_snapshot`` 聚合 M1-M5，
    各层失败隔离降级。
    """

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def build_snapshot(
        self,
        baby_id: str,
        family_id: str,
        *,
        baseline_window_days: int = 14,
        short_context_hours: int = 72,
        correction_query: str | None = None,
        correction_k: int = 5,
    ) -> MemorySnapshot:
        """聚合 M1-M5 → MemorySnapshot。

        ``correction_query``：M5 检索 query（通常为用户当前问题/意图）；None 则跳过 M5。
        各层失败隔离：异常降级为 None/空列表，记 warning，不抛出。
        """
        hard_facts = await self._safe(self._store.m1(baby_id), "M1")
        family_prefs = await self._safe(self._store.m2(family_id), "M2")
        baseline = await self._safe(self._store.m3(baby_id, baseline_window_days), "M3")
        short_context = await self._safe(self._store.m4(baby_id, short_context_hours), "M4")
        corrections = []
        if correction_query:
            corrections = (
                await self._safe(self._store.m5_search(correction_query, correction_k), "M5") or []
            )

        return MemorySnapshot(
            hard_facts=hard_facts,
            family_prefs=family_prefs,
            baseline=baseline,
            short_context=short_context,
            corrections=corrections,
            rule_version=None,  # T019 接入后由 Orchestrator 填充
        )

    @staticmethod
    async def _safe(coro, label: str):
        """单层失败隔离：异常降级为 None，记 warning。"""
        try:
            return await coro
        except Exception as e:
            logger.warning("memory.%s failed, degraded: %s", label, e)
            return None


__all__ = ["MemoryInjector"]
