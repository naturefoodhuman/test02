# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:05:00


"""APC-T009 ObservationEvent contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from server.app.events.domain.observation_event import EventSource, ObservationEventCreate


def _event_payload() -> dict[str, object]:
    now = datetime(2026, 7, 9, tzinfo=UTC)
    return {
        "event_id": "01KX15EVENT00000000000000",
        "baby_id": "01KX15BABY00000000000000",
        "family_id": "01KX15FAMILY00000000000",
        "event_type": "feeding",
        "start_time": now,
        "client_created_at": now,
        "source": EventSource.MANUAL,
        "payload": {"amount_ml": 90},
    }


def test_observation_event_accepts_sync_contract() -> None:
    event = ObservationEventCreate.model_validate(_event_payload())

    assert event.event_type == "feeding"
    assert event.source == "manual"
    assert event.payload == {"amount_ml": 90}


def test_observation_event_rejects_naive_datetime() -> None:
    payload = _event_payload()
    payload["start_time"] = datetime(2026, 7, 9)

    with pytest.raises(ValidationError, match="timezone-aware"):
        ObservationEventCreate.model_validate(payload)
