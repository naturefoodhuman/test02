# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:05:00


"""APC-T009 in-memory event repository tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from server.app.common.errors import ConflictError
from server.app.events.domain.observation_event import (
    EventCorrectionRequest,
    EventSource,
    ObservationEventCreate,
)
from server.app.events.infra.repository import InMemoryEventRepository


def _create_event(event_id: str = "01KX15EVENT00000000000000") -> ObservationEventCreate:
    now = datetime(2026, 7, 9, tzinfo=UTC)
    return ObservationEventCreate(
        event_id=event_id,
        baby_id="baby-1",
        family_id="family-1",
        event_type="feeding",
        start_time=now,
        client_created_at=now,
        source=EventSource.MANUAL,
        payload={"amount_ml": 90},
    )


@pytest.mark.asyncio
async def test_upsert_is_idempotent_for_same_event_identity() -> None:
    repo = InMemoryEventRepository()
    event = _create_event()

    first = await repo.upsert(event)
    second = await repo.upsert(event)

    assert first is second
    assert len(repo.events) == 1


@pytest.mark.asyncio
async def test_upsert_conflicts_for_same_id_different_baby() -> None:
    repo = InMemoryEventRepository()
    await repo.upsert(_create_event())
    changed = _create_event()
    changed.baby_id = "baby-2"

    with pytest.raises(ConflictError):
        await repo.upsert(changed)


@pytest.mark.asyncio
async def test_correction_and_soft_delete_keep_event_lineage() -> None:
    repo = InMemoryEventRepository()
    original = await repo.upsert(_create_event())

    corrected = await repo.correct(
        original.event_id,
        EventCorrectionRequest(normalized_payload={"amount_ml": 100}),
    )
    deleted = await repo.soft_delete(original.event_id)
    visible = await repo.list_by_baby("baby-1")
    all_events = await repo.list_by_baby("baby-1", include_deleted=True)

    assert corrected.correction_of == original.event_id
    assert corrected.normalized_payload == {"amount_ml": 100}
    assert deleted.is_deleted is True
    assert [event.event_id for event in visible] == [corrected.event_id]
    assert {event.event_id for event in all_events} == {original.event_id, corrected.event_id}
