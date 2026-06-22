# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:18:00

"""Unit tests for PIIReplacer (E5-C6-S1-T1)."""

from _infra.network.privacy_gateway.models import PIIEntity, PIIType
from _infra.network.privacy_gateway.replacer import InMemoryPIIMapStore, PIIReplacer


def entity(entity_type: PIIType, value: str, text: str, recognizer: str = "test") -> PIIEntity:
    start = text.index(value)
    return PIIEntity(
        type=entity_type,
        value=value,
        start=start,
        end=start + len(value),
        score=0.95,
        recognizer=recognizer,
    )


def entity_at(entity_type: PIIType, value: str, start: int, recognizer: str = "test") -> PIIEntity:
    return PIIEntity(
        type=entity_type,
        value=value,
        start=start,
        end=start + len(value),
        score=0.95,
        recognizer=recognizer,
    )


def test_replace_single_entity():
    text = "Contact Alice for details."
    replacer = PIIReplacer()

    result = replacer.replace(text, [entity(PIIType.PERSON, "Alice", text)])

    assert result.text == "Contact PII_PERSON_001 for details."
    assert "Alice" not in result.text
    assert result.placeholders == ["PII_PERSON_001"]
    assert result.mapping["PII_PERSON_001"].value == "Alice"


def test_replace_multiple_entities_sorted_by_offsets():
    text = "Alice works at OpenAI in San Francisco."
    entities = [
        entity(PIIType.LOCATION, "San Francisco", text),
        entity(PIIType.PERSON, "Alice", text),
        entity(PIIType.ORGANIZATION, "OpenAI", text),
    ]

    result = PIIReplacer().replace(text, entities)

    assert result.text == "PII_PERSON_001 works at PII_ORGANIZATION_002 in PII_LOCATION_003."
    assert "Alice" not in result.text
    assert "OpenAI" not in result.text
    assert "San Francisco" not in result.text


def test_same_value_reuses_placeholder():
    text = "Alice emailed Alice again."
    first = entity_at(PIIType.PERSON, "Alice", 0)
    second = entity_at(PIIType.PERSON, "Alice", text.rindex("Alice"))

    result = PIIReplacer().replace(text, [first, second])

    assert result.text == "PII_PERSON_001 emailed PII_PERSON_001 again."
    assert result.placeholders == ["PII_PERSON_001"]
    assert result.mapping["PII_PERSON_001"].value == "Alice"


def test_custom_placeholder_format():
    text = "API key sk-proj-abcdefghijklmnopqrstuvwxyz123456 leaked."
    pii = entity(PIIType.API_KEY, "sk-proj-abcdefghijklmnopqrstuvwxyz123456", text)
    replacer = PIIReplacer(placeholder_format="<<{entity_type}_{index:02d}>>")

    result = replacer.replace(text, [pii])

    assert result.text == "API key <<API_KEY_01>> leaked."
    assert result.placeholders == ["<<API_KEY_01>>"]


def test_mapping_id_and_queryable_mapping_store():
    text = "Phone 13812345678"
    store = InMemoryPIIMapStore()
    replacer = PIIReplacer(store=store)

    result = replacer.replace(text, [entity(PIIType.CN_PHONE, "13812345678", text)], mapping_id="map-1")

    assert result.mapping_id == "map-1"
    assert store.has("map-1") is True
    stored = replacer.get_mapping("map-1")
    assert stored["PII_CN_PHONE_001"].value == "13812345678"
    assert stored["PII_CN_PHONE_001"].type == PIIType.CN_PHONE


def test_empty_entities_stores_empty_mapping():
    store = InMemoryPIIMapStore()
    result = PIIReplacer(store=store).replace("No PII", [], mapping_id="empty")

    assert result.text == "No PII"
    assert result.mapping == {}
    assert result.entities == []
    assert store.has("empty") is True
    assert store.get("empty") == {}


def test_overlapping_entities_keep_first_longest_span():
    text = "Token ghp_abcdefghijklmnopqrstuvwxyz123456 leaked"
    long_value = "ghp_abcdefghijklmnopqrstuvwxyz123456"
    overlapping_value = "abcdefghijklmnopqrstuvwxyz123456"
    long_entity = entity(PIIType.API_KEY, long_value, text, recognizer="regex:github_pat")
    overlap_start = text.index(overlapping_value)
    overlap_entity = entity_at(PIIType.ACCESS_TOKEN, overlapping_value, overlap_start)

    result = PIIReplacer().replace(text, [overlap_entity, long_entity])

    assert result.text == "Token PII_API_KEY_001 leaked"
    assert len(result.mapping) == 1
    assert result.mapping["PII_API_KEY_001"].value == long_value


def test_invalid_zero_length_entity_is_ignored():
    text = "Alice"
    bad = PIIEntity(type=PIIType.PERSON, value="Alice", start=2, end=2)

    result = PIIReplacer().replace(text, [bad])

    assert result.text == "Alice"
    assert result.mapping == {}


def test_replacement_does_not_mutate_original_entities():
    text = "Alice"
    original = entity(PIIType.PERSON, "Alice", text)

    result = PIIReplacer().replace(text, [original])

    assert result.entities[0] is original
    assert original.value == "Alice"
    assert result.text == "PII_PERSON_001"
