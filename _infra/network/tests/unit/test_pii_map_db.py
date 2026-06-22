# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:32:00

"""Unit tests for encrypted PII Map DB (E5-C6-S1-T2)."""

import importlib.util
import sqlite3

import pytest

from _infra.network.privacy_gateway.models import PIIType
from _infra.network.privacy_gateway.pii_map_db import (
    PIIMapDB,
    PIIMapDBUnavailableError,
    PIIMapDecryptionError,
)
from _infra.network.privacy_gateway.replacer import PIIPlaceholderMapping


KEY = "test-key-at-least-16-chars"
WRONG_KEY = "wrong-key-at-least-16-chars"


def sample_mapping():
    return {
        "PII_PERSON_001": PIIPlaceholderMapping(
            placeholder="PII_PERSON_001",
            type=PIIType.PERSON,
            value="Alice",
            recognizer="spacy:PERSON",
            score=0.91,
        ),
        "PII_API_KEY_002": PIIPlaceholderMapping(
            placeholder="PII_API_KEY_002",
            type=PIIType.API_KEY,
            value="sk-proj-abcdefghijklmnopqrstuvwxyz123456",
            recognizer="regex:openai_key",
            score=0.98,
        ),
    }


def test_pii_map_db_save_get_roundtrip(tmp_path):
    db = PIIMapDB(tmp_path / "pii_map.db", KEY)
    db.save("map-1", sample_mapping())

    loaded = db.get("map-1")

    assert loaded["PII_PERSON_001"].value == "Alice"
    assert loaded["PII_PERSON_001"].type == PIIType.PERSON
    assert loaded["PII_API_KEY_002"].value.startswith("sk-proj-")
    assert db.has("map-1") is True


def test_pii_map_db_wrong_key_cannot_decrypt(tmp_path):
    path = tmp_path / "pii_map.db"
    db = PIIMapDB(path, KEY)
    db.save("map-1", sample_mapping())

    wrong = PIIMapDB(path, WRONG_KEY)

    with pytest.raises(PIIMapDecryptionError):
        wrong.get("map-1")


def test_pii_map_db_file_does_not_contain_plaintext(tmp_path):
    path = tmp_path / "pii_map.db"
    db = PIIMapDB(path, KEY)
    db.save("map-1", sample_mapping())

    raw = path.read_bytes()
    assert b"Alice" not in raw
    assert b"sk-proj-abcdefghijklmnopqrstuvwxyz123456" not in raw


def test_pii_map_db_get_original_and_delete(tmp_path):
    db = PIIMapDB(tmp_path / "pii_map.db", KEY)
    db.save("map-1", sample_mapping())

    assert db.get_original("map-1", "PII_PERSON_001") == "Alice"
    assert db.get_original("map-1", "missing") is None

    db.delete("map-1")
    assert db.has("map-1") is False
    assert db.get("map-1") == {}


def test_pii_map_db_save_replaces_existing_mapping(tmp_path):
    db = PIIMapDB(tmp_path / "pii_map.db", KEY)
    db.save("map-1", sample_mapping())
    db.save(
        "map-1",
        {
            "PII_PHONE_001": PIIPlaceholderMapping(
                placeholder="PII_PHONE_001",
                type=PIIType.PHONE_NUMBER,
                value="202-555-0123",
                recognizer="presidio:PHONE_NUMBER",
                score=0.8,
            )
        },
    )

    loaded = db.get("map-1")
    assert set(loaded) == {"PII_PHONE_001"}
    assert loaded["PII_PHONE_001"].value == "202-555-0123"


def test_pii_map_db_schema_created(tmp_path):
    path = tmp_path / "pii_map.db"
    PIIMapDB(path, KEY)

    with sqlite3.connect(path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'pii_mappings'"
        ).fetchall()
        columns = [row[1] for row in conn.execute("PRAGMA table_info(pii_mappings)").fetchall()]

    assert tables == [("pii_mappings",)]
    assert "id" in columns
    assert "placeholder" in columns
    assert "original" in columns


def test_require_sqlcipher_behavior(tmp_path):
    sqlcipher_available = importlib.util.find_spec("sqlcipher3") is not None or importlib.util.find_spec("pysqlcipher3") is not None
    if sqlcipher_available:
        db = PIIMapDB(tmp_path / "pii_map.db", KEY, require_sqlcipher=True)
        assert db.driver_name in {"sqlcipher3", "pysqlcipher3"}
    else:
        with pytest.raises(PIIMapDBUnavailableError):
            PIIMapDB(tmp_path / "pii_map.db", KEY, require_sqlcipher=True)


def test_short_key_is_rejected(tmp_path):
    with pytest.raises(PIIMapDBUnavailableError):
        PIIMapDB(tmp_path / "pii_map.db", "short")
