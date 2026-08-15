# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""语音文本解析单元测试（APC-T013，voice_text source）。

验证 ``parse_voice``：
    - feeding："刚喂了90ml奶" → amount_ml=90。
    - diaper："湿尿布"/"拉了屎"/"尿了屎" → wet/dirty/mixed。
    - temperature："体温38度5" → 38.5。
    - supplement："吃了维生素D" → name=维生素D。
    - sleep：无额外字段，full confidence。
    - normalized_payload 已有字段优先（不从文本重复解析）。
    - 解析失败降级 partial confidence。
    - event_type 不在 P0 → None。
"""

from __future__ import annotations

from datetime import UTC, datetime

from server.app.normalization.parsers.voice import (
    VOICE_CONFIDENCE_FULL,
    VOICE_CONFIDENCE_PARTIAL,
    parse_voice,
)

NOW = datetime(2026, 8, 13, 8, 0, 0, tzinfo=UTC)
EID = "01HZXKQW7P0QJ9V8R3M4N6H5T2"
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"


# ---- feeding ----


def test_feeding_from_text():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        raw_input={"text": "刚喂了90ml奶"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec is not None
    assert rec.table == "feeding_log"
    assert rec.payload["amount_ml"] == 90
    assert rec.confidence == VOICE_CONFIDENCE_FULL
    assert rec.structured["amount_ml"] == 90


def test_feeding_normalized_payload_takes_precedence():
    """normalized_payload 已有 amount_ml，不从文本解析（避免覆盖）。"""
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        raw_input={"text": "刚喂了90ml奶"},
        normalized_payload={"amount_ml": 150},
        start_time=NOW,
    )
    assert rec.payload["amount_ml"] == 150


def test_feeding_no_amount_in_text_degrades():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        raw_input={"text": "喂了点奶"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == VOICE_CONFIDENCE_PARTIAL
    assert rec.structured["amount_ml"] is None


def test_feeding_milliliter_unit():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        raw_input={"text": "喝了120毫升"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["amount_ml"] == 120


# ---- diaper ----


def test_diaper_wet():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="diaper",
        raw_input={"text": "换了个湿尿布"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["type"] == "wet"
    assert rec.confidence == VOICE_CONFIDENCE_FULL


def test_diaper_dirty():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="diaper",
        raw_input={"text": "拉了屎"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["type"] == "dirty"


def test_diaper_mixed():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="diaper",
        raw_input={"text": "又尿又拉了"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["type"] == "mixed"


def test_diaper_no_match_degrades():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="diaper",
        raw_input={"text": "看了一下"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == VOICE_CONFIDENCE_PARTIAL
    assert "type" not in rec.payload


# ---- temperature ----


def test_temperature_decimal():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="temperature",
        raw_input={"text": "体温38度5"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["value_c"] == 38.5
    assert rec.confidence == VOICE_CONFIDENCE_FULL


def test_temperature_plain():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="temperature",
        raw_input={"text": "37.2度"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["value_c"] == 37.2


def test_temperature_no_match_degrades():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="temperature",
        raw_input={"text": "量了一下"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == VOICE_CONFIDENCE_PARTIAL


# ---- supplement ----


def test_supplement_name():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="supplement",
        raw_input={"text": "吃了维生素D"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.payload["name"] == "维生素D"
    assert rec.confidence == VOICE_CONFIDENCE_FULL


def test_supplement_no_match_degrades():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="supplement",
        raw_input={"text": "嗯了一下"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.confidence == VOICE_CONFIDENCE_PARTIAL


# ---- sleep ----


def test_sleep_full_confidence_no_extra_fields():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="sleep",
        raw_input={"text": "宝宝睡了"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec.table == "sleep_log"
    assert rec.confidence == VOICE_CONFIDENCE_FULL


# ---- 边界 ----


def test_unknown_event_type_returns_none():
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="milestone",
        raw_input={"text": "会翻身了"},
        normalized_payload={},
        start_time=NOW,
    )
    assert rec is None


def test_no_text_uses_normalized_payload():
    """raw_input 无 text，normalized_payload 有字段 → 用 normalized_payload。"""
    rec = parse_voice(
        event_id=EID,
        baby_id=BABY,
        event_type="feeding",
        raw_input=None,
        normalized_payload={"amount_ml": 100},
        start_time=NOW,
    )
    assert rec.payload["amount_ml"] == 100
    assert rec.confidence == VOICE_CONFIDENCE_FULL
