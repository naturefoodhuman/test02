# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
#
# app/normalization/service.py —— Normalization 服务（APC-T013）。
# 依据：ENGINEERING_DESIGN §2 M05、§7.1（NOTIFY events.changed → Normalization 写 feeding_log）；
#       ARCHITECTURE_FINAL §4.1；TASK_BACKLOG APC-T013。
# 设计：NormalizationService.normalize(event) 按 source 路由到 form/voice parser，
#       产出 NormalizedRecord → 写对应 *_log 派生表 → 推进 processing_status=normalized。
#       不识别事件（event_type 不在 P0）保留 observation_event，processing_status 不推进
#       （架构 §7.1 不丢记录；Worker 可后续扩展支持更多 event_type）。
#       幂等：重复 normalize 同一 event_id 不重复写派生表（按 event_id 查 log 表去重）。
# 边界：不做医疗判断；不产生告警；派生表保留 event_id FK 溯源（架构 §6.1）。

"""Normalization 服务（APC-T013）。

架构（ENGINEERING_DESIGN §2 M05 / §7.1）：
``NormalizationService.normalize(event)`` 按 ``source`` 路由到 ``form`` / ``voice``
parser，产出 ``NormalizedRecord`` → 写对应 ``*_log`` 派生表 → 推进
``processing_status=normalized``。

不识别事件（``event_type`` 不在 P0 范围）保留 ``observation_event``，
``processing_status`` 不推进（架构 §7.1 不丢记录；Worker 可后续扩展）。

幂等：重复 ``normalize`` 同一 ``event_id`` 不重复写派生表（按 ``event_id`` 查 log 表去重）。

边界：不做医疗判断；不产生告警；派生表保留 ``event_id`` FK 溯源（架构 §6.1）。
"""

from __future__ import annotations

import logging
from typing import Protocol

from ..common.errors import NotFoundError
from ..events.domain import (
    ObservationEvent,
    ObservationEventRepository,
    ProcessingStatus,
    Source,
)
from .domain import NormalizedRecord
from .parsers import parse_form, parse_voice

_logger = logging.getLogger(__name__)


class LogWriter(Protocol):
    """派生表写入协议（APC-T013）。

    按 ``NormalizedRecord.table`` 写对应 ``*_log`` 表；幂等（按 ``event_id`` 去重）。
    实现见 ``normalization.infra.log_writer.SqlAlchemyLogWriter``。
    """

    async def exists(self, event_id: str, table: str) -> bool:
        """``event_id`` 是否已在 ``table`` 派生表存在（幂等去重）。"""
        ...

    async def write(self, record: NormalizedRecord) -> None:
        """写 ``NormalizedRecord`` 到对应 ``*_log`` 表（幂等：已存在则跳过）。"""
        ...


class NormalizationService:
    """Normalization 用例服务（APC-T013）。

    消费 ``ObservationEvent``，按 ``source`` 路由到 parser，写派生表并推进
    ``processing_status=normalized``。依赖 ``ObservationEventRepository``（读/更新事件）
    与 ``LogWriter``（写派生表），共享同一 ``AsyncSession``（事务边界在 service 层）。
    """

    def __init__(
        self,
        *,
        repository: ObservationEventRepository,
        log_writer: LogWriter,
    ) -> None:
        self._repo = repository
        self._log_writer = log_writer

    async def normalize(self, event: ObservationEvent) -> NormalizedRecord | None:
        """归一化单个事件 → 写派生表 + 推进 processing_status=normalized。

        Returns:
            ``NormalizedRecord``（已写入派生表）；event_type 不在 P0 范围返回 ``None``
            （保留事件，不推进 processing_status）。

        Raises:
            NotFoundError: 事件不存在或已软删除（调用方应跳过）。
        """
        record = self._parse(event)
        if record is None:
            _logger.info(
                "normalize.skip",
                extra={"event_id": event.event_id, "event_type": event.event_type},
            )
            return None
        # 幂等：派生表已有该 event_id 行则跳过写入，但仍推进 processing_status（保证最终一致）。
        if not await self._log_writer.exists(record.event_id, record.table):
            await self._log_writer.write(record)
        updated = await self._repo.update_processing_status(
            event.event_id, ProcessingStatus.NORMALIZED
        )
        if updated is None:
            raise NotFoundError(
                f"Event {event.event_id} not found or soft-deleted during normalization",
                evidence={"event_id": event.event_id},
            )
        _logger.info(
            "normalize.done",
            extra={
                "event_id": event.event_id,
                "table": record.table,
                "confidence": record.confidence,
            },
        )
        return record

    def _parse(self, event: ObservationEvent) -> NormalizedRecord | None:
        """按 source 路由到 form/voice parser。"""
        if event.source == Source.MANUAL:
            return parse_form(
                event_id=event.event_id,
                baby_id=event.baby_id,
                event_type=event.event_type,
                normalized_payload=event.normalized_payload,
                start_time=event.start_time,
                end_time=event.end_time,
            )
        if event.source == Source.VOICE_TEXT:
            return parse_voice(
                event_id=event.event_id,
                baby_id=event.baby_id,
                event_type=event.event_type,
                raw_input=event.raw_input,
                normalized_payload=event.normalized_payload,
                start_time=event.start_time,
                end_time=event.end_time,
            )
        # camera/sensor/ai/system：P0 不归一化（留待对应领域任务）。
        return None


__all__ = ["LogWriter", "NormalizationService"]
