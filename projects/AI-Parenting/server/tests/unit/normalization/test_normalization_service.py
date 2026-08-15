# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""NormalizationService 单元测试（APC-T013）。

验证：
    - manual feeding 事件 → 写 feeding_log + 推进 processing_status=normalized。
    - voice_text feeding 事件 → 写 feeding_log（低置信）。
    - 不识别 event_type（camera/sensor/ai/system 或非 P0）→ None，不写派生表、不推进。
    - 幂等：派生表已有 event_id 行 → 跳过 write，仍推进 processing_status。
    - 事件不存在 → NotFoundError。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from server.app.common.errors import NotFoundError
from server.app.events.domain import (
    ObservationEvent,
    ProcessingStatus,
    Source,
    SyncStatus,
)
from server.app.normalization.domain import NormalizedRecord
from server.app.normalization.service import NormalizationService

NOW = datetime(2026, 8, 13, 8, 0, 0, tzinfo=UTC)
EID = "01HZXKQW7P0QJ9V8R3M4N6H5T2"
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"
FAM = "01HZXKQW7P0QJ9V8R3M4N6H5T4"


class FakeEventRepository:
    """内存事件仓储替身（实现 update_processing_status）。"""

    def __init__(self) -> None:
        self.updated: list[tuple[str, ProcessingStatus]] = []

    async def update_processing_status(
        self, event_id: str, status: ProcessingStatus
    ) -> ObservationEvent | None:
        self.updated.append((event_id, status))
        return ObservationEvent(
            event_id=event_id,
            baby_id=BABY,
            family_id=FAM,
            event_type="feeding",
            start_time=NOW,
            client_created_at=NOW,
            server_received_at=NOW,
            normalized_payload={"amount_ml": 120},
            source=Source.MANUAL,
            sync_status=SyncStatus.SYNCED,
            processing_status=status,
        )


class FakeLogWriter:
    """内存派生表写入替身。"""

    def __init__(self, *, existing: set[str] | None = None) -> None:
        self.existing: set[str] = existing or set()
        self.written: list[NormalizedRecord] = []

    async def exists(self, event_id: str, table: str) -> bool:
        return f"{table}:{event_id}" in self.existing

    async def write(self, record: NormalizedRecord) -> None:
        self.written.append(record)
        self.existing.add(f"{record.table}:{record.event_id}")


def _feeding_event(source: Source = Source.MANUAL, **payload_overrides) -> ObservationEvent:
    payload = {"amount_ml": 120}
    payload.update(payload_overrides)
    return ObservationEvent(
        event_id=EID,
        baby_id=BABY,
        family_id=FAM,
        event_type="feeding",
        start_time=NOW,
        client_created_at=NOW,
        server_received_at=NOW,
        normalized_payload=payload,
        source=source,
        sync_status=SyncStatus.SYNCED,
        processing_status=ProcessingStatus.PENDING,
    )


async def test_manual_feeding_writes_log_and_advances_status():
    repo = FakeEventRepository()
    writer = FakeLogWriter()
    svc = NormalizationService(repository=repo, log_writer=writer)

    record = await svc.normalize(_feeding_event())

    assert record is not None
    assert record.table == "feeding_log"
    assert len(writer.written) == 1
    assert writer.written[0].event_id == EID
    assert repo.updated == [(EID, ProcessingStatus.NORMALIZED)]


async def test_voice_feeding_writes_log_lower_confidence():
    repo = FakeEventRepository()
    writer = FakeLogWriter()
    svc = NormalizationService(repository=repo, log_writer=writer)

    ev = ObservationEvent(
        event_id=EID,
        baby_id=BABY,
        family_id=FAM,
        event_type="feeding",
        start_time=NOW,
        client_created_at=NOW,
        server_received_at=NOW,
        normalized_payload={},
        raw_input={"text": "刚喂了90ml奶"},
        source=Source.VOICE_TEXT,
        sync_status=SyncStatus.SYNCED,
        processing_status=ProcessingStatus.PENDING,
    )
    record = await svc.normalize(ev)

    assert record is not None
    assert record.confidence < 1.0
    assert record.structured["amount_ml"] == 90
    assert len(writer.written) == 1


async def test_idempotent_skip_write_but_still_advance_status():
    repo = FakeEventRepository()
    writer = FakeLogWriter(existing={"feeding_log:" + EID})
    svc = NormalizationService(repository=repo, log_writer=writer)

    record = await svc.normalize(_feeding_event())

    assert record is not None
    assert len(writer.written) == 0  # 已存在，跳过写入。
    assert repo.updated == [(EID, ProcessingStatus.NORMALIZED)]  # 仍推进状态。


@pytest.mark.parametrize("source", [Source.CAMERA, Source.SENSOR, Source.AI, Source.SYSTEM])
async def test_non_p0_source_returns_none_no_write_no_advance(source: Source):
    repo = FakeEventRepository()
    writer = FakeLogWriter()
    svc = NormalizationService(repository=repo, log_writer=writer)

    record = await svc.normalize(_feeding_event(source=source))

    assert record is None
    assert len(writer.written) == 0
    assert repo.updated == []


async def test_non_p0_event_type_returns_none():
    repo = FakeEventRepository()
    writer = FakeLogWriter()
    svc = NormalizationService(repository=repo, log_writer=writer)

    ev = ObservationEvent(
        event_id=EID,
        baby_id=BABY,
        family_id=FAM,
        event_type="milestone",
        start_time=NOW,
        client_created_at=NOW,
        server_received_at=NOW,
        normalized_payload={},
        source=Source.MANUAL,
        sync_status=SyncStatus.SYNCED,
        processing_status=ProcessingStatus.PENDING,
    )
    record = await svc.normalize(ev)

    assert record is None
    assert len(writer.written) == 0
    assert repo.updated == []


async def test_event_not_found_raises():
    class _MissingRepo(FakeEventRepository):
        async def update_processing_status(self, event_id, status):
            self.updated.append((event_id, status))
            return None

    repo = _MissingRepo()
    writer = FakeLogWriter()
    svc = NormalizationService(repository=repo, log_writer=writer)

    with pytest.raises(NotFoundError):
        await svc.normalize(_feeding_event())
