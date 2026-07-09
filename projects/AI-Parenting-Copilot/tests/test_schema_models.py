# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 00:30:00


"""APC-T004 schema metadata tests."""

from __future__ import annotations

from pathlib import Path

import server.app.models  # noqa: F401 - import registers models with Base.metadata
from server.app.db import Base

REQUIRED_TABLES = {
    "family",
    "user",
    "device",
    "baby",
    "observation_event",
    "feeding_log",
    "diaper_log",
    "sleep_log",
    "temperature_log",
    "supplement_log",
    "vaccine_record",
    "growth_log",
    "medication_log",
    "symptom_event",
    "jaundice_photo",
    "milestone_log",
    "solid_food_log",
    "mother_health",
    "derived_baby_state",
    "alert",
    "alert_delivery",
    "sleep_session",
    "family_knowledge",
    "evidence_policy",
    "sensor_event",
    "camera_event",
    "media_asset",
    "audit_log",
    "sync_state",
}


def test_core_metadata_contains_required_tables() -> None:
    assert REQUIRED_TABLES.issubset(set(Base.metadata.tables))


def test_observation_event_contract_and_indexes_exist() -> None:
    table = Base.metadata.tables["observation_event"]

    assert table.primary_key.columns.keys() == ["event_id"]
    assert {"sync_status", "processing_status", "is_deleted"}.issubset(table.columns.keys())
    index_names = {index.name for index in table.indexes}
    assert "ix_observation_event_baby_type_start" in index_names


def test_audit_log_append_only_sql_present_in_migration() -> None:
    migration = (
        Path(__file__).resolve().parents[1] / "server/migrations/versions/0001_initial_schema.py"
    ).read_text()

    assert "prevent_audit_log_mutation" in migration
    assert "REVOKE UPDATE, DELETE ON TABLE audit_log" in migration
    assert "trg_audit_log_no_delete" in migration
