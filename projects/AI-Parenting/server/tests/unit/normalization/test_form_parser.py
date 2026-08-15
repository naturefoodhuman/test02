# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""表单解析单元测试（APC-T013，manual source）。

验证 ``parse_form``：
    - feeding：amount_ml/feeding_type/started_at/ended_at 结构化列 + payload 兜底。
    - diaper/sleep/temperature/supplement：无结构化列，业务字段入 payload。
    - confidence=1.0（manual）；缺关键字段降级 0.6。
    - event_type 不在 P0 范围 → None。
    - amount_ml 类型转换（int/float→int，bool 排除）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from server.app.normalization.parsers.form import (
    MANUAL_CONFIDENCE,
    PARTIAL_CONFIDENCE,
    parse_form,
)

NOW = datetime(2026, 8, 13, 8, 0, 0, tzinfo=UTC)
EID = "01HZXKQW7P0QJ9V8R3M4N6H5T2"
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"


def test_feeding_full_payload_structured_columns():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        normalized_payload={"amount_ml": 120, "feeding_type": "bottle"},
        start_time=NOW,
        end_time=NOW,
    )
    assert rec is not None
    assert rec.table == "feeding_log"
    assert rec.confidence == MANUAL_CONFIDENCE
    assert rec.structured == {
        "amount_ml": 120,
        "feeding_type": "bottle",
        "started_at": NOW,
        "ended_at": NOW,
    }
    assert rec.payload == {"amount_ml": 120, "feeding_type": "bottle"}
    assert rec.event_id == EID
    assert rec.baby_id == BABY


def test_feeding_missing_amount_degrades_confidence():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        normalized_payload={"feeding_type": "breast"},
        start_time=NOW,
    )
    assert rec is not None
    assert rec.confidence == PARTIAL_CONFIDENCE
    assert rec.structured["amount_ml"] is None


def test_amount_ml_float_to_int():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        normalized_payload={"amount_ml": 120.0},
        start_time=NOW,
    )
    assert rec.structured["amount_ml"] == 120


def test_amount_ml_non_integer_float_becomes_none():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        normalized_payload={"amount_ml": 120.5},
        start_time=NOW,
    )
    assert rec.structured["amount_ml"] is None


def test_amount_ml_bool_excluded():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        normalized_payload={"amount_ml": True},
        start_time=NOW,
    )
    assert rec.structured["amount_ml"] is None


def test_diaper_no_structured_columns():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="diaper",
        normalized_payload={"type": "wet"},
        start_time=NOW,
    )
    assert rec is not None
    assert rec.table == "diaper_log"
    assert rec.structured == {}
    assert rec.payload == {"type": "wet"}
    assert rec.confidence == MANUAL_CONFIDENCE


def test_diaper_missing_type_degrades():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="diaper",
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == PARTIAL_CONFIDENCE


def test_sleep_always_full_confidence():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="sleep",
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.table == "sleep_log"
    assert rec.confidence == MANUAL_CONFIDENCE


def test_temperature_value_c():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="temperature",
        normalized_payload={"value_c": 37.2},
        start_time=NOW,
    )
    assert rec.table == "temperature_log"
    assert rec.confidence == MANUAL_CONFIDENCE
    assert rec.payload == {"value_c": 37.2}


def test_temperature_missing_value_degrades():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="temperature",
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == PARTIAL_CONFIDENCE


def test_supplement_name():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="supplement",
        normalized_payload={"name": "维生素D"},
        start_time=NOW,
    )
    assert rec.table == "supplement_log"
    assert rec.confidence == MANUAL_CONFIDENCE


def test_supplement_supplement_name_alias():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="supplement",
        normalized_payload={"supplement_name": "DHA"},
        start_time=NOW,
    )
    assert rec.confidence == MANUAL_CONFIDENCE


def test_supplement_missing_name_degrades():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="supplement",
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == PARTIAL_CONFIDENCE


def test_unknown_event_type_returns_none():
    rec = parse_form(
        event_id=EID,
        baby_id=BABY,
        event_type="milestone",
        normalized_payload={},
        start_time=NOW,
    )
    assert rec is None
