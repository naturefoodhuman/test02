# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-12 00:00:00
"""PowerSync 同步契约校验单元测试（APC-T012 测试要求：Unit 契约缺字段拒绝）。

验证 ``validate_sync_contract``：
    - 合法记录 → 返回 ObservationEvent（sync_status=synced, processing_status=pending）。
    - 缺必填字段 → ValidationError（evidence.missing 列出缺失字段）。
    - ULID 非法 → ValidationError。
    - source 非法 → ValidationError。
    - payload 非 dict → ValidationError。
    - confidence 越界 / 类型错 → ValidationError。
    - start_time 缺失时回退到 client_created_at。
    - datetime 接受 ISO 字符串或 datetime 对象。
    - 非法记录不进入 EventService（本测试只校验 validator 行为，不调 service）。

依据：ENGINEERING_DESIGN §6.3（同步契约字段）、§9.1（不自研同步）；
      ARCHITECTURE_FINAL §9.2；TASK_BACKLOG APC-T012。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from server.app.common.errors import ValidationError
from server.app.events.domain import ProcessingStatus, Source, SyncStatus
from server.app.sync.service.contract_validator import validate_sync_contract

NOW = datetime(2026, 8, 11, 8, 0, 0, tzinfo=UTC)
EID = "01HZXKQW7P0QJ9V8R3M4N6H5T2"
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"
FAM = "01HZXKQW7P0QJ9V8R3M4N6H5T4"


def _valid_record(**overrides) -> dict:
    """构造合法同步契约记录（§6.3 字段）。"""
    base = {
        "event_id": EID,
        "baby_id": BABY,
        "family_id": FAM,
        "event_type": "feeding",
        "client_created_at": NOW.isoformat(),
        "payload": {"amount_ml": 120},
        "source": "manual",
    }
    base.update(overrides)
    return base


# ---- 合法路径 ----


def test_valid_record_returns_event_synced_pending():
    ev = validate_sync_contract(_valid_record())
    assert ev.event_id == EID
    assert ev.baby_id == BABY
    assert ev.family_id == FAM
    assert ev.event_type == "feeding"
    assert ev.source == Source.MANUAL
    assert ev.normalized_payload == {"amount_ml": 120}
    # 上行成功 → synced；processing_status=pending（独立状态机，§6.2）。
    assert ev.sync_status == SyncStatus.SYNCED
    assert ev.processing_status == ProcessingStatus.PENDING
    # server_received_at 由服务端覆盖（此处占位，service 会重置，§6.3）；
    # validator 用 epoch 占位，不依赖具体时区（service.record 会用 Clock 重置）。
    assert ev.server_received_at is not None
    assert ev.server_received_at.year == 1970
    # client_created_at 由 ISO 字符串解析为 datetime。
    assert ev.client_created_at == NOW
    # start_time 缺失时回退到 client_created_at。
    assert ev.start_time == NOW
    # 可选字段默认值。
    assert ev.is_deleted is False
    assert ev.attachments == []
    assert ev.correction_of is None
    assert ev.confidence == 1.0


def test_valid_record_with_datetime_object():
    """client_created_at 接受 datetime 对象（非仅 ISO 字符串）。"""
    ev = validate_sync_contract(_valid_record(client_created_at=NOW))
    assert ev.client_created_at == NOW


def test_valid_record_start_time_explicit():
    """显式 start_time 优先于 client_created_at 回退。"""
    later = datetime(2026, 8, 11, 8, 5, 0, tzinfo=UTC)
    ev = validate_sync_contract(_valid_record(start_time=later.isoformat()))
    assert ev.start_time == later


def test_valid_record_optional_fields_passed_through():
    ev = validate_sync_contract(
        _valid_record(
            user_id="01HZXKQW7P0QJ9V8R3M4N6H5T5",
            device_id="01HZXKQW7P0QJ9V8R3M4N6H5T6",
            end_time=NOW.isoformat(),
            raw_input={"text": "喂了90ml"},
            confidence=0.8,
            attachments=["01HZMEDIA000000000000001"],
            correction_of="01HZXKQW7P0QJ9V8R3M4N6H5T7",
            is_deleted=False,
        )
    )
    assert ev.user_id == "01HZXKQW7P0QJ9V8R3M4N6H5T5"
    assert ev.device_id == "01HZXKQW7P0QJ9V8R3M4N6H5T6"
    assert ev.end_time == NOW
    assert ev.raw_input == {"text": "喂了90ml"}
    assert ev.confidence == 0.8
    assert ev.attachments == ["01HZMEDIA000000000000001"]
    assert ev.correction_of == "01HZXKQW7P0QJ9V8R3M4N6H5T7"


# ---- 缺必填字段 ----


@pytest.mark.parametrize(
    "missing_field",
    ["event_id", "baby_id", "family_id", "event_type", "client_created_at", "payload", "source"],
)
def test_missing_required_field_raises(missing_field: str):
    record = _valid_record()
    del record[missing_field]
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    assert "missing" in str(exc.value).lower() or missing_field in str(exc.value)


def test_missing_multiple_fields_lists_all():
    record = _valid_record()
    del record["event_type"]
    del record["payload"]
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    # evidence 含 missing 列表（至少含两个缺失字段）。
    ev = exc.value
    missing = (ev.evidence or {}).get("missing", [])
    assert "event_type" in missing
    assert "payload" in missing


# ---- ULID 校验 ----


@pytest.mark.parametrize("field", ["event_id", "baby_id", "family_id"])
def test_invalid_ulid_raises(field: str):
    record = _valid_record(**{field: "not-a-ulid"})
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    assert field in str(exc.value)


# ---- source 合法性 ----


def test_invalid_source_raises():
    record = _valid_record(source="invalid_source")
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    assert "source" in str(exc.value).lower()


@pytest.mark.parametrize("src", ["manual", "voice_text", "camera", "sensor", "ai", "system"])
def test_all_valid_sources_accepted(src: str):
    ev = validate_sync_contract(_valid_record(source=src))
    assert ev.source.value == src


# ---- payload ----


def test_payload_not_dict_raises():
    record = _valid_record(payload="not-a-dict")
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    assert "payload" in str(exc.value).lower()


def test_payload_null_raises():
    # payload=None 缺必填（not in record after del）。
    record = _valid_record()
    record["payload"] = None
    with pytest.raises(ValidationError):
        validate_sync_contract(record)


# ---- confidence ----


@pytest.mark.parametrize("bad", [-0.1, 1.1, 2.0, -1, "high"])
def test_confidence_out_of_range_or_wrong_type_raises(bad):
    record = _valid_record(confidence=bad)
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    assert "confidence" in str(exc.value).lower()


@pytest.mark.parametrize("good", [0.0, 0.5, 1.0, 0, 1])
def test_confidence_boundary_accepted(good):
    ev = validate_sync_contract(_valid_record(confidence=good))
    assert ev.confidence == float(good)


# ---- datetime 解析 ----


def test_invalid_iso_datetime_raises():
    record = _valid_record(client_created_at="not-a-date")
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    assert "client_created_at" in str(exc.value)


def test_missing_client_created_at_raises():
    record = _valid_record()
    del record["client_created_at"]
    with pytest.raises(ValidationError) as exc:
        validate_sync_contract(record)
    # 缺必填字段走必填检查（evidence.missing 列出），而非 _parse_dt 的 required 检查。
    missing = (exc.value.evidence or {}).get("missing", [])
    assert "client_created_at" in missing


def test_non_dict_record_raises():
    with pytest.raises(ValidationError):
        validate_sync_contract("not-a-dict")  # type: ignore[arg-type]


# ---- 非法记录不进入业务（验收）----


def test_invalid_record_returns_none_or_raises_not_event():
    """非法记录必须被 validator 拦截（ValidationError），绝不返回 ObservationEvent
    进入 EventService（验收：非法同步事件不会进入业务处理）。"""
    record = _valid_record()
    del record["event_id"]
    with pytest.raises(ValidationError):
        validate_sync_contract(record)
