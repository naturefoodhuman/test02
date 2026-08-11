# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
"""ORM 模型元数据单元测试（APC-T004，不连 DB）。

校验表/列/约束/索引元数据对齐 ENGINEERING_DESIGN §6.1/§6.2 与 §5.1。
"""

from __future__ import annotations

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from server.app.models import (
    Alert,
    AlertDelivery,
    AuditLog,
    Baby,
    CameraEvent,
    DerivedBabyState,
    Device,
    DiaperLog,
    EvidencePolicy,
    Family,
    FamilyKnowledge,
    FeedingLog,
    MediaAsset,
    ObservationEvent,
    SensorEvent,
    SleepSession,
    SyncState,
    User,
)


def _cols(table):
    return {c.name for c in table.columns}


def _check_constraints(table):
    return {c.name for c in table.constraints if isinstance(c, CheckConstraint)}


def _fk_constraints(table):
    return {c for c in table.constraints if isinstance(c, ForeignKeyConstraint)}


def _unique_constraints(table):
    return {c for c in table.constraints if isinstance(c, UniqueConstraint)}


def test_all_28_business_tables_registered():
    """28 张业务表全部注册到 Base.metadata（§6.1）。"""
    from server.app.models import Base

    tables = set(Base.metadata.tables.keys())
    expected = {
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
        "medication_log",
        "symptom_event",
        "jaundice_photo",
        "milestone_log",
        "growth_log",
        "solid_food_log",
        "media_asset",
        "derived_baby_state",
        "alert",
        "alert_delivery",
        "sleep_session",
        "sensor_event",
        "camera_event",
        "family_knowledge",
        "evidence_policy",
        "audit_log",
        "sync_state",
    }
    assert expected <= tables, f"missing: {expected - tables}"


def test_ulid_primary_keys_are_string_26():
    """所有 ULID PK 表的主键为 String(26)（§6.2 ULID 统一）。"""
    for cls in [Family, User, Device, Baby, ObservationEvent, FeedingLog, Alert, AuditLog]:
        pk = cls.__table__.primary_key.columns[0]
        assert pk.type.length == 26, f"{cls.__name__} PK length != 26"


def test_observation_event_fields_align_section_5_1():
    """ObservationEvent 字段对齐 §5.1 数据契约。"""
    cols = _cols(ObservationEvent.__table__)
    for required in [
        "id",
        "baby_id",
        "family_id",
        "user_id",
        "device_id",
        "event_type",
        "start_time",
        "end_time",
        "client_created_at",
        "server_received_at",
        "raw_input",
        "normalized_payload",
        "confidence",
        "source",
        "attachments",
        "correction_of",
        "is_deleted",
        "sync_status",
        "processing_status",
    ]:
        assert required in cols, f"observation_event missing {required}"


def test_observation_event_check_constraints():
    """ObservationEvent 的 source/sync_status/processing_status 枚举约束（§5.1/§6.2）。"""
    checks = _check_constraints(ObservationEvent.__table__)
    assert "ck_observation_event_source" in checks
    assert "ck_observation_event_sync_status" in checks
    assert "ck_observation_event_processing_status" in checks


def test_observation_event_index_baby_type_start():
    """§6.1 索引 idx(baby_id, event_type, start_time DESC)。"""
    idx_names = {i.name for i in ObservationEvent.__table__.indexes}
    assert "ix_observation_event_baby_type_start" in idx_names


def test_baby_fields_align_section_6_1():
    """Baby 字段对齐 §6.1。"""
    cols = _cols(Baby.__table__)
    for required in [
        "id",
        "family_id",
        "birth_date",
        "gestational_age_weeks",
        "is_preterm",
        "birth_weight_g",
        "current_weight_g",
        "current_weight_at",
        "sex",
        "vaccine_region",
        "allergies",
        "is_deleted",
    ]:
        assert required in cols, f"baby missing {required}"


def test_device_kind_check_constraint():
    """device.kind 枚举 phone/camera/mmwave/mac（§6.1）。"""
    checks = _check_constraints(Device.__table__)
    assert "ck_device_kind" in checks


def test_alert_level_check_constraint():
    """alert.level 枚举 gray/blue/yellow/orange/red（§6.1）。"""
    checks = _check_constraints(Alert.__table__)
    assert "ck_alert_level" in checks
    assert "ck_alert_status" in checks


def test_evidence_policy_unique_constraint():
    """evidence_policy (policy_type,region,version) UNIQUE（§6.2 规则版本化）。"""
    uniques = _unique_constraints(EvidencePolicy.__table__)
    assert any(tuple(u.columns.keys()) == ("policy_type", "region", "version") for u in uniques), (
        "evidence_policy missing (policy_type,region,version) unique"
    )


def test_family_knowledge_unique_family_key():
    """family_knowledge (family_id, key) UNIQUE。"""
    uniques = _unique_constraints(FamilyKnowledge.__table__)
    assert any(tuple(u.columns.keys()) == ("family_id", "key") for u in uniques)


def test_audit_log_is_append_only_no_soft_delete():
    """audit_log 不含 is_deleted（append-only，§22.2）。"""
    cols = _cols(AuditLog.__table__)
    assert "is_deleted" not in cols
    assert "ts" in cols and "actor" in cols and "action" in cols and "resource" in cols
    assert "before" in cols and "after" in cols and "rule_version" in cols and "llm_call_id" in cols


def test_sync_state_client_id_primary_key():
    """sync_state 以 client_id 为主键（§6.1）。"""
    pk = SyncState.__table__.primary_key.columns[0]
    assert pk.name == "client_id"


def test_derived_baby_state_baby_id_primary_key():
    """derived_baby_state 以 baby_id 为主键（§6.1 upsert 当前快照）。"""
    pk = DerivedBabyState.__table__.primary_key.columns[0]
    assert pk.name == "baby_id"
    cols = _cols(DerivedBabyState.__table__)
    assert "snapshot" in cols and "computed_at" in cols


def test_log_tables_have_event_id_fk():
    """各 *_log 含 event_id FK 溯源 observation_event（§6.1）。"""
    for cls in [FeedingLog, DiaperLog]:
        fks = _fk_constraints(cls.__table__)
        assert any(
            any(fk.column.table.name == "observation_event" for fk in c.elements) for c in fks
        ), f"{cls.__name__} missing event_id FK to observation_event"


def test_feeding_log_has_structured_p0_columns():
    """feeding_log 含 P0 端到端结构化列（amount_ml/feeding_type/started_at/ended_at）。"""
    cols = _cols(FeedingLog.__table__)
    for required in [
        "amount_ml",
        "feeding_type",
        "started_at",
        "ended_at",
        "event_id",
        "baby_id",
        "payload",
    ]:
        assert required in cols, f"feeding_log missing {required}"


def test_sensor_event_and_camera_event_no_soft_delete():
    """sensor_event/camera_event 不可删除（证据溯源，无 is_deleted）。"""
    assert "is_deleted" not in _cols(SensorEvent.__table__)
    assert "is_deleted" not in _cols(CameraEvent.__table__)


def test_alert_delivery_no_soft_delete():
    """alert_delivery 不可删除（送达审计）。"""
    assert "is_deleted" not in _cols(AlertDelivery.__table__)


def test_media_asset_stores_path_not_blob():
    """media_asset 存路径不存二进制（架构 §7 大文件不入库）。"""
    cols = _cols(MediaAsset.__table__)
    assert "asset_path" in cols
    assert "blob" not in cols and "data" not in cols


@pytest.mark.parametrize(
    "cls",
    [
        Family,
        User,
        Device,
        Baby,
        ObservationEvent,
        FeedingLog,
        Alert,
        FamilyKnowledge,
        EvidencePolicy,
    ],
)
def test_timestamped_tables_have_created_updated(cls):
    """含 TimestampMixin 的表有 created_at/updated_at（timezone-aware）。"""
    cols = _cols(cls.__table__)
    assert "created_at" in cols
    assert "updated_at" in cols
    # timezone-aware 列。
    assert cls.__table__.c.created_at.type.timezone is True
    assert cls.__table__.c.updated_at.type.timezone is True


@pytest.mark.parametrize(
    "cls",
    [Family, User, Device, Baby, ObservationEvent, FeedingLog, DiaperLog, Alert, SleepSession],
)
def test_soft_delete_tables_have_is_deleted(cls):
    """含 SoftDeleteMixin 的表有 is_deleted（§6.2 软删除）。"""
    assert "is_deleted" in _cols(cls.__table__)
