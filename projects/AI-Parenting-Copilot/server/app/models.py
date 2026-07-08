# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 00:30:00


"""SQLAlchemy metadata for the AI Parenting Copilot core schema.

This module is the application-side model counterpart to Alembic revision
`0001_initial_schema`. It intentionally contains table metadata only; repository
behavior is introduced by later tasks.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid
from server.app.db import Base

JsonDict = dict[str, Any]


class TimestampMixin:
    """Common created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class SoftDeleteMixin:
    """Common soft-delete flag required by event-sourced tables."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Family(TimestampMixin, Base):
    __tablename__ = "family"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai", nullable=False)


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    auth_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Device(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "device"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Baby(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "baby"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gestational_age_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_preterm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    birth_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_weight_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    vaccine_region: Mapped[str] = mapped_column(String(16), default="CN", nullable=False)
    allergies: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class ObservationEvent(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "observation_event"
    __table_args__ = (
        Index("ix_observation_event_baby_type_start", "baby_id", "event_type", "start_time"),
        Index("ix_observation_event_processing", "processing_status"),
    )

    event_id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    baby_id: Mapped[str] = mapped_column(ForeignKey("baby.id"), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    device_id: Mapped[str | None] = mapped_column(
        ForeignKey("device.id"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    raw_input: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    normalized_payload: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    attachments: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    correction_of: Mapped[str | None] = mapped_column(
        ForeignKey("observation_event.event_id"), nullable=True, index=True
    )
    sync_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)


class EventDerivedTableMixin(TimestampMixin, SoftDeleteMixin):
    """Common fields for normalized domain tables."""

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    event_id: Mapped[str] = mapped_column(
        ForeignKey("observation_event.event_id"), unique=True, nullable=False
    )
    baby_id: Mapped[str] = mapped_column(ForeignKey("baby.id"), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    payload: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class FeedingLog(EventDerivedTableMixin, Base):
    __tablename__ = "feeding_log"

    fed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    amount_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feeding_type: Mapped[str | None] = mapped_column(String(32), nullable=True)


class DiaperLog(EventDerivedTableMixin, Base):
    __tablename__ = "diaper_log"

    changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    diaper_type: Mapped[str | None] = mapped_column(String(32), nullable=True)


class SleepLog(EventDerivedTableMixin, Base):
    __tablename__ = "sleep_log"

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TemperatureLog(EventDerivedTableMixin, Base):
    __tablename__ = "temperature_log"

    measured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    value_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[str | None] = mapped_column(String(32), nullable=True)


class SupplementLog(EventDerivedTableMixin, Base):
    __tablename__ = "supplement_log"

    supplement_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)


class VaccineRecord(EventDerivedTableMixin, Base):
    __tablename__ = "vaccine_record"

    vaccine_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MedicationLog(EventDerivedTableMixin, Base):
    __tablename__ = "medication_log"

    medication_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dose_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    dose_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SymptomEvent(EventDerivedTableMixin, Base):
    __tablename__ = "symptom_event"

    symptom_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)


class JaundicePhoto(EventDerivedTableMixin, Base):
    __tablename__ = "jaundice_photo"

    media_asset_id: Mapped[str | None] = mapped_column(String(26), nullable=True)


class MilestoneLog(EventDerivedTableMixin, Base):
    __tablename__ = "milestone_log"

    milestone_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GrowthLog(EventDerivedTableMixin, Base):
    __tablename__ = "growth_log"

    measured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    head_circumference_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)


class SolidFoodLog(EventDerivedTableMixin, Base):
    __tablename__ = "solid_food_log"

    food_name: Mapped[str | None] = mapped_column(String(200), nullable=True)


class MotherHealth(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "mother_health"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class DerivedBabyState(TimestampMixin, Base):
    __tablename__ = "derived_baby_state"

    baby_id: Mapped[str] = mapped_column(ForeignKey("baby.id"), primary_key=True)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    snapshot: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class Alert(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "alert"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    baby_id: Mapped[str] = mapped_column(ForeignKey("baby.id"), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    ack_by: Mapped[str | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class AlertDelivery(TimestampMixin, Base):
    __tablename__ = "alert_delivery"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alert.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    receipt: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class SleepSession(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "sleep_session"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    baby_id: Mapped[str] = mapped_column(ForeignKey("baby.id"), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    roi_config: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class FamilyKnowledge(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "family_knowledge"
    __table_args__ = (Index("ix_family_knowledge_key", "family_id", "key"),)

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class EvidencePolicy(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "evidence_policy"
    __table_args__ = (
        Index("uq_evidence_policy_current", "policy_type", "region", "version", unique=True),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    hash: Mapped[str] = mapped_column(String(128), nullable=False)


class SensorEvent(TimestampMixin, Base):
    __tablename__ = "sensor_event"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    device_id: Mapped[str] = mapped_column(ForeignKey("device.id"), nullable=False, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class CameraEvent(TimestampMixin, Base):
    __tablename__ = "camera_event"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("device.id"), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sleep_session.id"), nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    clip_path: Mapped[str | None] = mapped_column(Text, nullable=True)


class MediaAsset(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "media_asset"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    family_id: Mapped[str] = mapped_column(ForeignKey("family.id"), nullable=False, index=True)
    baby_id: Mapped[str | None] = mapped_column(ForeignKey("baby.id"), nullable=True, index=True)
    event_id: Mapped[str | None] = mapped_column(
        ForeignKey("observation_event.event_id"), nullable=True
    )
    local_path: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    camera_id: Mapped[str | None] = mapped_column(ForeignKey("device.id"), nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tags: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    meta: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=new_ulid)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    actor: Mapped[JsonDict] = mapped_column(JSONB, default=dict, nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    before_state: Mapped[JsonDict | None] = mapped_column("before", JSONB, nullable=True)
    after_state: Mapped[JsonDict | None] = mapped_column("after", JSONB, nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SyncState(TimestampMixin, Base):
    __tablename__ = "sync_state"

    client_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    family_id: Mapped[str | None] = mapped_column(
        ForeignKey("family.id"), nullable=True, index=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pending_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
