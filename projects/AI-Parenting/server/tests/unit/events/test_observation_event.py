# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""ObservationEvent 领域契约单元测试（APC-T009 测试要求：Unit Pydantic 校验）。

验证 ``ObservationEvent`` Pydantic 契约：
    - 必填字段缺失 → ValidationError（pydantic）。
    - Source/SyncStatus/ProcessingStatus 枚举值合法/非法。
    - confidence 越界（<0 / >1）→ 校验失败。
    - extra 字段 → 拒绝（extra="forbid"）。
    - frozen=True：实例不可变。
    - 默认值：is_deleted=False、sync_status=PENDING、processing_status=PENDING、attachments=[]。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from server.app.events.domain import (
    ObservationEvent,
    ProcessingStatus,
    Source,
    SyncStatus,
)

NOW = datetime(2026, 8, 11, 0, 0, 0, tzinfo=UTC)


def _valid_kwargs(**overrides):
    base = {
        "event_id": "01HZXKQW7P0QJ9V8R3M4N6H5T2",
        "baby_id": "01HZXKQW7P0QJ9V8R3M4N6H5T3",
        "family_id": "01HZXKQW7P0QJ9V8R3M4N6H5T4",
        "event_type": "feeding",
        "start_time": NOW,
        "client_created_at": NOW,
        "server_received_at": NOW,
        "normalized_payload": {"amount_ml": 120},
        "source": Source.MANUAL,
    }
    base.update(overrides)
    return base


class TestObservationEventContract:
    """§5.1 数据契约 SSOT 校验。"""

    def test_minimal_valid_event(self):
        ev = ObservationEvent(**_valid_kwargs())
        assert ev.event_id == "01HZXKQW7P0QJ9V8R3M4N6H5T2"
        assert ev.user_id is None
        assert ev.device_id is None
        assert ev.end_time is None
        assert ev.raw_input is None
        assert ev.confidence == 1.0
        assert ev.attachments == []
        assert ev.correction_of is None
        assert ev.is_deleted is False
        assert ev.sync_status == SyncStatus.PENDING
        assert ev.processing_status == ProcessingStatus.PENDING

    def test_missing_required_field_raises(self):
        for field in (
            "event_id",
            "baby_id",
            "family_id",
            "event_type",
            "start_time",
            "client_created_at",
            "server_received_at",
            "normalized_payload",
            "source",
        ):
            kwargs = _valid_kwargs()
            del kwargs[field]
            with pytest.raises(PydanticValidationError):
                ObservationEvent(**kwargs)

    def test_source_enum_values(self):
        for src in Source:
            ev = ObservationEvent(**_valid_kwargs(source=src))
            assert ev.source == src

    @pytest.mark.parametrize("bad_source", ["", "web", "MANUAL", "manual "])
    def test_invalid_source_rejected(self, bad_source):
        with pytest.raises(PydanticValidationError):
            ObservationEvent(**_valid_kwargs(source=bad_source))

    def test_sync_status_enum(self):
        for s in SyncStatus:
            ev = ObservationEvent(**_valid_kwargs(sync_status=s))
            assert ev.sync_status == s

    def test_processing_status_enum(self):
        for s in ProcessingStatus:
            ev = ObservationEvent(**_valid_kwargs(processing_status=s))
            assert ev.processing_status == s

    @pytest.mark.parametrize("bad_conf", [-0.01, 1.01, -1, 2])
    def test_confidence_out_of_range_rejected(self, bad_conf):
        with pytest.raises(PydanticValidationError):
            ObservationEvent(**_valid_kwargs(confidence=bad_conf))

    @pytest.mark.parametrize("ok_conf", [0.0, 0.5, 1.0])
    def test_confidence_boundary_accepted(self, ok_conf):
        ev = ObservationEvent(**_valid_kwargs(confidence=ok_conf))
        assert ev.confidence == ok_conf

    def test_extra_field_forbidden(self):
        with pytest.raises(PydanticValidationError):
            ObservationEvent(**_valid_kwargs(unexpected="x"))

    def test_frozen_immutable(self):
        ev = ObservationEvent(**_valid_kwargs())
        with pytest.raises(PydanticValidationError):
            ev.event_id = "other"  # type: ignore[misc]

    def test_correction_of_preserved(self):
        ev = ObservationEvent(**_valid_kwargs(correction_of="01HZXKQW7P0QJ9V8R3M4N6H5T9"))
        assert ev.correction_of == "01HZXKQW7P0QJ9V8R3M4N6H5T9"

    def test_attachments_default_empty_list(self):
        ev = ObservationEvent(**_valid_kwargs())
        assert ev.attachments == []

    def test_normalized_payload_required_dict(self):
        ev = ObservationEvent(**_valid_kwargs(normalized_payload={"k": "v"}))
        assert ev.normalized_payload == {"k": "v"}
