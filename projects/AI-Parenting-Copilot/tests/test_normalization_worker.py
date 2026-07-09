# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""APC-T014 normalization worker/dedup tests."""

from __future__ import annotations

from server.app.normalization.dedup import apply_correction, is_duplicate_feeding
from server.app.normalization.service import NormalizationService, NormalizedRecord


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
