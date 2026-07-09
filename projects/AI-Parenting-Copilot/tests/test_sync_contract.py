# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00

"""APC-T012 sync contract validator tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from server.app.sync.service.contract_validator import (
    SyncContractError,
    feeding_duplicate_hint,
    validate_sync_record,
)


def _record(event_id: str, created_at: datetime) -> dict[str, object]:
    return {
        "event_id": event_id,
        "baby_id": "baby-1",
        "family_id": "family-1",
        "user_id": "user-1",
        "device_id": "device-1",
        "event_type": "feeding",
        "client_created_at": created_at.isoformat(),
        "payload": {"amount_ml": 90},
        "source": "manual",
        "confidence": 1.0,
        "is_deleted": False,
        "correction_of": None,
    }


def test_sync_contract_missing_fields_rejected() -> None:
    with pytest.raises(SyncContractError):
        validate_sync_record({"event_id": "e1"})


def test_valid_sync_contract_and_duplicate_feeding_soft_hint() -> None:
    now = datetime(2026, 7, 9, tzinfo=UTC)
    first = _record("e1", now)
    second = _record("e2", now + timedelta(minutes=4))

    validate_sync_record(first)
    hint = feeding_duplicate_hint([first, second])

    assert hint is not None
    assert hint.kind == "duplicate_feeding_soft_hint"
    assert hint.event_ids == ["e1", "e2"]
