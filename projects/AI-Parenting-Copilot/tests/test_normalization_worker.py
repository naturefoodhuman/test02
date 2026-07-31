# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""APC-T014 normalization worker/dedup tests."""

from __future__ import annotations

from server.app.normalization.dedup import apply_correction, is_duplicate_feeding
from server.app.normalization.service import NormalizationService, NormalizedRecord
from server.app.normalization.sqlalchemy_store import build_derived_row_values
from server.app.normalization.worker import to_asyncpg_url


def test_scan_pending_is_idempotent_for_repeated_events() -> None:
    from tests.test_normalization_p0 import _event

    event = _event("feeding", {"amount_ml": 90})
    service = NormalizationService()
    first = service.scan_pending([event])
    second = service.scan_pending([event])

    assert len(first) == 1
    assert second == []


def test_dedup_and_correction_helpers() -> None:
    first = NormalizedRecord(
        event_id="e1",
        baby_id="b",
        family_id="f",
        record_type="feeding",
        payload={},
    )
    second = NormalizedRecord(
        event_id="e2",
        baby_id="b",
        family_id="f",
        record_type="feeding",
        payload={},
        correction_of="e1",
    )

    assert is_duplicate_feeding(first, second)
    assert apply_correction([first, second]) == [second]


def test_sqlalchemy_store_maps_feeding_record_to_typed_columns() -> None:
    from tests.test_normalization_p0 import _event

    event = _event("feeding", {"amount_ml": 90, "feeding_type": "formula"})
    record = NormalizationService().normalize(event)
    assert record is not None

    model, values = build_derived_row_values(record, event)

    assert model.__tablename__ == "feeding_log"
    assert values["event_id"] == event.event_id
    assert values["amount_ml"] == 90
    assert values["feeding_type"] == "formula"
    assert values["fed_at"] == event.start_time


def test_to_asyncpg_url_accepts_sqlalchemy_async_url() -> None:
    assert to_asyncpg_url("postgresql+asyncpg://u:p@localhost/db") == "postgresql://u:p@localhost/db"
