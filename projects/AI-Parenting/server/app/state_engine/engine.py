# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/engine.py —— Baby State Engine 重算服务（APC-T016）。
# 依据：ENGINEERING_DESIGN §2 M06（事件驱动增量派生；幂等重算）、§6.3、§7.1；
#       ARCHITECTURE_FINAL §10.1（输入 ObservationEvent 增量、幂等重算、只派生不告警）；
#       TASK_BACKLOG APC-T016（重算幂等；全量+事件触发增量；snapshot 含 computed_at 与 source event range；
#       processing_status 可推进到 projected）。
# 设计：StateEngine.recompute(baby_id, now) 全量重算——加载该 baby 未删除事件 → project_state
#       → upsert snapshot。幂等：同一事件集 + 同一 now 多次重算结果一致（project_state 纯函数 + upsert 覆盖）。
#       增量重算 = 事件触发时调 recompute（T017 接 NormalizationWorker 之后）。
#       processing_status 推进 projected：重算成功后推进该 baby 所有 normalized 事件到 projected
#       （§6.2 双状态机：processing_status pending→normalized→projected）。
# 边界：只派生不告警；不做医疗判断；不读派生表（消费事件本身）。

"""Baby State Engine 重算服务（APC-T016）。

架构（ENGINEERING_DESIGN §2 M06 / §10.1）：
``StateEngine.recompute(baby_id, now)`` 全量重算——加载该 baby 未删除事件 →
``project_state`` → ``snapshot_repo.upsert``。幂等（纯函数 + upsert 覆盖）。

增量重算：事件触发时（Normalization 完成后，T017）调 ``recompute``，按 baby 全量重算
（P0 量级全量重算开销可接受；真正增量优化在后续任务）。

``processing_status`` 推进 projected（§6.2）：重算成功后推进该 baby 所有 ``normalized``
事件到 ``projected``，标记已进入派生快照。与 ``sync_status`` 独立（双状态机）。
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from ..common.clock import Clock
from ..events.domain import ObservationEvent, ObservationEventRepository, ProcessingStatus
from .domain import DerivedBabyState
from .project import project_state
from .snapshot_repo import SnapshotRepository

_logger = logging.getLogger(__name__)


@runtime_checkable
class EventLoader(Protocol):
    """按 baby 加载未删除事件的协议（engine 依赖，便于测试注入替身）。"""

    async def load_by_baby(self, baby_id: str) -> list[ObservationEvent]:
        """加载该 baby 所有未删除事件（按 start_time 升序）。"""
        ...


class StateEngine:
    """Baby State Engine 重算服务（APC-T016）。

    依赖注入 ``EventLoader``（按 baby 加载事件）、``SnapshotRepository``（快照 upsert/get）、
    ``ObservationEventRepository``（推进 processing_status）、``Clock``（参考时间）。
    事务边界在调用方（service / worker），本服务 flush 不 commit（架构 §5.2）。
    """

    def __init__(
        self,
        *,
        event_loader: EventLoader,
        snapshot_repo: SnapshotRepository,
        event_repo: ObservationEventRepository,
        clock: Clock,
    ) -> None:
        self._event_loader = event_loader
        self._snapshot_repo = snapshot_repo
        self._event_repo = event_repo
        self._clock = clock

    async def recompute(self, baby_id: str, now=None) -> DerivedBabyState:
        """全量重算 baby 派生状态并 upsert 快照（幂等，APC-T016）。

        Args:
            baby_id: 婴儿 ULID。
            now: 参考时间；None 则取 clock.now()。

        Returns:
            重算后的 ``DerivedBabyState``（已 upsert 到 derived_baby_state）。
        """
        if now is None:
            now = self._clock.now()
        events = await self._event_loader.load_by_baby(baby_id)
        state = project_state(events, now)
        await self._snapshot_repo.upsert(baby_id, state)
        # 推进该 baby 所有 normalized 事件到 projected（§6.2 双状态机）。
        # 全量重算后该 baby 的事件已进入派生快照，标记 projected。
        for event in events:
            if event.processing_status == ProcessingStatus.NORMALIZED:
                await self._event_repo.update_processing_status(
                    event.event_id, ProcessingStatus.PROJECTED
                )
        _logger.info(
            "state_engine.recompute.done baby_id=%s events=%d computed_at=%s",
            baby_id,
            len(events),
            now.isoformat(),
        )
        return state

    async def get_state(self, baby_id: str) -> DerivedBabyState | None:
        """读取 baby 最新派生快照（只读，供 State API）。"""
        return await self._snapshot_repo.get(baby_id)


__all__ = ["EventLoader", "StateEngine"]
