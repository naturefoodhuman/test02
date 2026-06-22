# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:45:00

"""Unit tests for Privacy Gateway output schema validation (E5-C7-S1-T1)."""

import pytest

from _infra.network.exceptions import SchemaValidationFailedError
from _infra.network.privacy_gateway.models import PIIType
from _infra.network.privacy_gateway.replacer import PIIPlaceholderMapping
from _infra.network.privacy_gateway.validator import (
    DEFAULT_SCHEMA_PATH,
    PrivacyOutputValidator,
    build_privacy_output,
    safe_entity_metadata,
    validate_privacy_output,
)


def valid_output():
    return {
        "text": "Contact PII_PERSON_001.",
        "mapping_id": "map-1",
        "entities": [
            {
                "type": "PERSON",
                "placeholder": "PII_PERSON_001",
                "recognizer": "spacy:PERSON",
                "score": 0.91,
                "start": 8,
                "end": 13,
            }
        ],
        "schema_valid": True,
        "canary_clean": True,
    }


def test_valid_output_passes_default_validator():
    output = valid_output()
    assert validate_privacy_output(output) == output


def test_minimal_valid_output_passes():
    output = {
        "text": "No PII",
        "mapping_id": "map-empty",
        "entities": [],
    }
    assert PrivacyOutputValidator().validate(output) == output


def test_missing_required_field_rejected():
    output = valid_output()
    output.pop("mapping_id")

    with pytest.raises(SchemaValidationFailedError) as exc_info:
        validate_privacy_output(output)

    assert exc_info.value.code == "SCHEMA_VALIDATION_FAILED"
    assert "mapping_id" in exc_info.value.message


def test_extra_top_level_field_rejected():
    output = valid_output()
    output["raw_text"] = "Alice"

    with pytest.raises(SchemaValidationFailedError):
        validate_privacy_output(output)


def test_raw_value_in_entity_rejected():
    output = valid_output()
    output["entities"][0]["value"] = "Alice"

    with pytest.raises(SchemaValidationFailedError):
        validate_privacy_output(output)


def test_invalid_entity_score_rejected():
    output = valid_output()
    output["entities"][0]["score"] = 1.5

    with pytest.raises(SchemaValidationFailedError):
        validate_privacy_output(output)


def test_invalid_type_rejected():
    with pytest.raises(SchemaValidationFailedError):
        validate_privacy_output(["not", "an", "object"])


def test_is_valid_helper():
    validator = PrivacyOutputValidator()
    assert validator.is_valid(valid_output()) is True
    assert validator.is_valid({"text": "x"}) is False


def test_load_schema_from_default_path():
    validator = PrivacyOutputValidator(schema_path=DEFAULT_SCHEMA_PATH)
    assert validator.is_valid(valid_output()) is True


def test_build_privacy_output_omits_raw_values():
    mapping = {
        "PII_PERSON_001": PIIPlaceholderMapping(
            placeholder="PII_PERSON_001",
            type=PIIType.PERSON,
            value="Alice",
            recognizer="spacy:PERSON",
            score=0.91,
        )
    }

    entities = safe_entity_metadata(mapping)
    output = build_privacy_output("Contact PII_PERSON_001.", "map-1", mapping, canary_clean=True)

    assert entities == [
        {
            "type": "PERSON",
            "placeholder": "PII_PERSON_001",
            "recognizer": "spacy:PERSON",
            "score": 0.91,
        }
    ]
    assert "Alice" not in str(output)
    assert validate_privacy_output(output) == output
