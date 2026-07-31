# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""APC-T013 normalization parser/service tests."""

from __future__ import annotations

from datetime import UTC, datetime

from server.app.events.domain.observation_event import (
    EventSource,
    ObservationEvent,
    ObservationEventCreate,
)
from server.app.normalization.parsers.voice import parse_voice_text
from server.app.normalization.service import NormalizationService


def _event(event_type: str, payload: dict[str, object]) -> ObservationEvent:
    now = datetime(2026, 7, 9, tzinfo=UTC)
    return ObservationEvent.model_validate(
        ObservationEventCreate(
            baby_id="baby-1",
            family_id="family-1",
            event_type=event_type,
            start_time=now,
            client_created_at=now,
            source=EventSource.MANUAL,
            payload=payload,
        ).model_dump()
    )


def test_voice_text_parses_p0_record_types() -> None:
    assert parse_voice_text("刚喂了90ml奶")[:2] == ("feeding", {"amount_ml": 90.0})
    assert parse_voice_text("体温37.8度")[0] == "temperature"
    assert parse_voice_text("换了尿布")[0] == "diaper"


def test_normalization_service_writes_derived_record_with_event_lineage() -> None:
    event = _event("feeding", {"amount_ml": 90})
    record = NormalizationService().normalize(event)

    assert record is not None
    assert record.event_id == event.event_id
    assert record.record_type == "feeding"
    assert event.processing_status == "normalized"


def test_voice_text_parser_supports_common_word_orders_and_spaces() -> None:
    assert parse_voice_text("80 毫升奶")[:2] == ("feeding", {"amount_ml": 80.0})
    assert parse_voice_text("奶 80 毫升")[:2] == ("feeding", {"amount_ml": 80.0})
    assert parse_voice_text("体温 39.5 ℃")[:2] == ("temperature", {"value_c": 39.5})
