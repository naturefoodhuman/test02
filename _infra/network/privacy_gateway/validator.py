# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:45:00

"""
Privacy Gateway output JSON Schema validator (E5-C7-S1-T1).

Per NETWORK_ARCHITECTURE_FINAL.md §10.1 and TASK_BACKLOG E5-C7-S1-T1.

The validator enforces the shape of redacted Privacy Gateway output before it is
allowed to leave the local pipeline. The default schema intentionally forbids
raw PII values inside ``entities``; only safe metadata such as placeholder,
entity type, recognizer and score is allowed.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator, ValidationError

from ..exceptions import SchemaValidationFailedError
from .replacer import PIIPlaceholderMapping

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "config" / "output_schemas" / "privacy_gateway_output.schema.yaml"


class PrivacyOutputValidator:
    """Validate Privacy Gateway output using JSON Schema."""

    def __init__(self, schema: Mapping[str, Any] | None = None, schema_path: str | Path | None = None):
        if schema is not None and schema_path is not None:
            raise ValueError("Provide either schema or schema_path, not both")

        self.schema_path = Path(schema_path) if schema_path is not None else None
        self.schema = dict(schema) if schema is not None else self.load_schema(self.schema_path or DEFAULT_SCHEMA_PATH)
        self._validator = Draft202012Validator(self.schema)

    @staticmethod
    def load_schema(path: str | Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
        """Load a JSON Schema from YAML or JSON file."""
        schema_path = Path(path)
        with schema_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise SchemaValidationFailedError(
                f"Schema file {schema_path} did not contain an object schema",
                schema_path=str(schema_path),
            )
        return data

    @staticmethod
    def _to_plain_data(output: Any) -> dict[str, Any]:
        if is_dataclass(output):
            output = asdict(output)
        if not isinstance(output, dict):
            raise SchemaValidationFailedError(
                "Privacy output must be a JSON object",
                output_type=type(output).__name__,
            )
        return output

    def validate(self, output: Any) -> dict[str, Any]:
        """Validate output or raise SchemaValidationFailedError."""
        data = self._to_plain_data(output)
        try:
            self._validator.validate(data)
        except ValidationError as exc:
            path = "/".join(str(part) for part in exc.absolute_path)
            schema_path = "/".join(str(part) for part in exc.absolute_schema_path)
            raise SchemaValidationFailedError(
                f"Privacy output schema validation failed: {exc.message}",
                validation_path=path,
                schema_path=schema_path,
                validator=exc.validator,
            ) from exc
        return data

    def is_valid(self, output: Any) -> bool:
        try:
            self.validate(output)
            return True
        except SchemaValidationFailedError:
            return False


# The module-level singleton keeps caller code simple while still allowing tests
# to instantiate validators with custom schemas.
DEFAULT_PRIVACY_OUTPUT_VALIDATOR = PrivacyOutputValidator()


def safe_entity_metadata(mapping: Mapping[str, PIIPlaceholderMapping]) -> list[dict[str, Any]]:
    """Convert placeholder mapping into schema-safe entity metadata.

    Raw original values are intentionally omitted.
    """
    entities: list[dict[str, Any]] = []
    for placeholder, entry in mapping.items():
        entities.append(
            {
                "type": entry.type.value,
                "placeholder": placeholder,
                "recognizer": entry.recognizer,
                "score": entry.score,
            }
        )
    return entities


def build_privacy_output(
    text: str,
    mapping_id: str,
    mapping: Mapping[str, PIIPlaceholderMapping],
    *,
    schema_valid: bool | None = None,
    canary_clean: bool | None = None,
) -> dict[str, Any]:
    """Build a schema-friendly redacted output dict without raw PII values."""
    output: dict[str, Any] = {
        "text": text,
        "mapping_id": mapping_id,
        "entities": safe_entity_metadata(mapping),
    }
    if schema_valid is not None:
        output["schema_valid"] = schema_valid
    if canary_clean is not None:
        output["canary_clean"] = canary_clean
    return output


def validate_privacy_output(output: Any) -> dict[str, Any]:
    """Validate with the default Privacy Gateway output schema."""
    return DEFAULT_PRIVACY_OUTPUT_VALIDATOR.validate(output)


__all__ = [
    "DEFAULT_PRIVACY_OUTPUT_VALIDATOR",
    "DEFAULT_SCHEMA_PATH",
    "PrivacyOutputValidator",
    "build_privacy_output",
    "safe_entity_metadata",
    "validate_privacy_output",
]
