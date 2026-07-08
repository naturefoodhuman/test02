# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 00:30:00

"""initial core schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-09 00:30:00 CST
"""

from __future__ import annotations

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _ulid_pk(name: str = "id") -> sa.Column[str]:
    return sa.Column(name, sa.String(length=26), primary_key=True)


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _soft_delete() -> sa.Column[bool]:
    return sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False)


def _jsonb(name: str, *, nullable: bool = False) -> sa.Column[object]:
    default = None if nullable else sa.text("'{}'::jsonb")
    return sa.Column(
        name, postgresql.JSONB(astext_type=sa.Text()), server_default=default, nullable=nullable
    )


def _event_domain_columns() -> list[sa.Column[object]]:
    return [
        _ulid_pk(),
        sa.Column("event_id", sa.String(length=26), nullable=False),
        sa.Column("baby_id", sa.String(length=26), nullable=False),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        _jsonb("payload"),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["event_id"], ["observation_event.event_id"]),
        sa.ForeignKeyConstraint(["baby_id"], ["baby.id"]),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
        sa.UniqueConstraint("event_id"),
    ]


def _create_domain_table(name: str, extras: Iterable[sa.Column[object]]) -> None:
    op.create_table(name, *_event_domain_columns(), *extras)
    op.create_index(f"ix_{name}_baby_id", name, ["baby_id"])
    op.create_index(f"ix_{name}_family_id", name, ["family_id"])


UPDATED_AT_TABLES = [
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
    "sync_state",
]


def _install_updated_at_triggers() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in UPDATED_AT_TABLES:
        trigger = f"trg_{table}_updated_at"
        op.execute(f'DROP TRIGGER IF EXISTS {trigger} ON "{table}";')
        op.execute(
            f'''
            CREATE TRIGGER {trigger}
            BEFORE UPDATE ON "{table}"
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
            '''
        )


def _install_audit_immutability() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute('DROP TRIGGER IF EXISTS trg_audit_log_no_update ON "audit_log";')
    op.execute('DROP TRIGGER IF EXISTS trg_audit_log_no_delete ON "audit_log";')
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_no_update
        BEFORE UPDATE ON "audit_log"
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_no_delete
        BEFORE DELETE ON "audit_log"
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                REVOKE UPDATE, DELETE ON TABLE audit_log FROM app_user;
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    op.create_table(
        "family",
        _ulid_pk(),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("timezone", sa.String(length=64), server_default="Asia/Shanghai", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "user",
        _ulid_pk(),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("auth_hash", sa.String(length=255), nullable=True),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_user_family_id", "user", ["family_id"])

    op.create_table(
        "device",
        _ulid_pk(),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("user_id", sa.String(length=26), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        _jsonb("meta"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_device_family_id", "device", ["family_id"])
    op.create_index("ix_device_user_id", "device", ["user_id"])

    op.create_table(
        "baby",
        _ulid_pk(),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("gestational_age_weeks", sa.Integer(), nullable=True),
        sa.Column("is_preterm", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("birth_weight_g", sa.Integer(), nullable=True),
        sa.Column("current_weight_g", sa.Integer(), nullable=True),
        sa.Column("current_weight_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sex", sa.String(length=16), nullable=True),
        sa.Column("vaccine_region", sa.String(length=16), server_default="CN", nullable=False),
        _jsonb("allergies"),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_baby_family_id", "baby", ["family_id"])

    op.create_table(
        "observation_event",
        sa.Column("event_id", sa.String(length=26), primary_key=True),
        sa.Column("baby_id", sa.String(length=26), nullable=False),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("user_id", sa.String(length=26), nullable=True),
        sa.Column("device_id", sa.String(length=26), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "server_received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        _jsonb("raw_input"),
        _jsonb("normalized_payload"),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        _jsonb("attachments"),
        sa.Column("correction_of", sa.String(length=26), nullable=True),
        sa.Column("sync_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column(
            "processing_status", sa.String(length=32), server_default="pending", nullable=False
        ),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["baby_id"], ["baby.id"]),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.ForeignKeyConstraint(["correction_of"], ["observation_event.event_id"]),
    )
    op.create_index("ix_observation_event_baby_id", "observation_event", ["baby_id"])
    op.create_index("ix_observation_event_family_id", "observation_event", ["family_id"])
    op.create_index("ix_observation_event_user_id", "observation_event", ["user_id"])
    op.create_index("ix_observation_event_device_id", "observation_event", ["device_id"])
    op.create_index("ix_observation_event_correction_of", "observation_event", ["correction_of"])
    op.create_index("ix_observation_event_processing", "observation_event", ["processing_status"])
    op.create_index(
        "ix_observation_event_baby_type_start",
        "observation_event",
        ["baby_id", "event_type", sa.text("start_time DESC")],
    )

    _create_domain_table(
        "feeding_log",
        [
            sa.Column("fed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("amount_ml", sa.Integer(), nullable=True),
            sa.Column("feeding_type", sa.String(length=32), nullable=True),
        ],
    )
    _create_domain_table(
        "diaper_log",
        [
            sa.Column("changed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("diaper_type", sa.String(length=32), nullable=True),
        ],
    )
    _create_domain_table(
        "sleep_log",
        [
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        ],
    )
    _create_domain_table(
        "temperature_log",
        [
            sa.Column("measured_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("value_c", sa.Float(), nullable=True),
            sa.Column("method", sa.String(length=32), nullable=True),
        ],
    )
    _create_domain_table(
        "supplement_log",
        [
            sa.Column("supplement_name", sa.String(length=100)),
            sa.Column("status", sa.String(length=32)),
        ],
    )
    _create_domain_table(
        "vaccine_record",
        [
            sa.Column("vaccine_name", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rule_version", sa.String(length=64), nullable=True),
        ],
    )
    _create_domain_table(
        "medication_log",
        [
            sa.Column("medication_name", sa.String(length=200), nullable=True),
            sa.Column("dose_mg", sa.Float(), nullable=True),
            sa.Column("dose_ml", sa.Float(), nullable=True),
            sa.Column("given_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rule_version", sa.String(length=64), nullable=True),
        ],
    )
    _create_domain_table(
        "symptom_event",
        [
            sa.Column("symptom_type", sa.String(length=100)),
            sa.Column("severity", sa.String(length=32)),
        ],
    )
    _create_domain_table(
        "jaundice_photo", [sa.Column("media_asset_id", sa.String(length=26), nullable=True)]
    )
    _create_domain_table(
        "milestone_log",
        [
            sa.Column("milestone_key", sa.String(length=100)),
            sa.Column("observed_at", sa.DateTime(timezone=True)),
        ],
    )
    _create_domain_table(
        "growth_log",
        [
            sa.Column("measured_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("weight_g", sa.Integer(), nullable=True),
            sa.Column("height_mm", sa.Integer(), nullable=True),
            sa.Column("head_circumference_mm", sa.Integer(), nullable=True),
        ],
    )
    _create_domain_table(
        "solid_food_log", [sa.Column("food_name", sa.String(length=200), nullable=True)]
    )

    op.create_table(
        "mother_health",
        _ulid_pk(),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        _jsonb("payload"),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_mother_health_family_id", "mother_health", ["family_id"])

    op.create_table(
        "derived_baby_state",
        sa.Column("baby_id", sa.String(length=26), primary_key=True),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        _jsonb("snapshot"),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(["baby_id"], ["baby.id"]),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_derived_baby_state_family_id", "derived_baby_state", ["family_id"])

    op.create_table(
        "alert",
        _ulid_pk(),
        sa.Column("baby_id", sa.String(length=26), nullable=False),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        _jsonb("evidence"),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("ack_by", sa.String(length=26), nullable=True),
        sa.Column("ack_at", sa.DateTime(timezone=True), nullable=True),
        _jsonb("feedback"),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["baby_id"], ["baby.id"]),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
        sa.ForeignKeyConstraint(["ack_by"], ["user.id"]),
    )
    op.create_index("ix_alert_baby_id", "alert", ["baby_id"])
    op.create_index("ix_alert_family_id", "alert", ["family_id"])

    op.create_table(
        "alert_delivery",
        _ulid_pk(),
        sa.Column("alert_id", sa.String(length=26), nullable=False),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        _jsonb("receipt"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["alert_id"], ["alert.id"]),
    )
    op.create_index("ix_alert_delivery_alert_id", "alert_delivery", ["alert_id"])

    op.create_table(
        "sleep_session",
        _ulid_pk(),
        sa.Column("baby_id", sa.String(length=26), nullable=False),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        _jsonb("roi_config"),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["baby_id"], ["baby.id"]),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_sleep_session_baby_id", "sleep_session", ["baby_id"])
    op.create_index("ix_sleep_session_family_id", "sleep_session", ["family_id"])

    op.create_table(
        "family_knowledge",
        _ulid_pk(),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        _jsonb("value"),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_family_knowledge_family_id", "family_knowledge", ["family_id"])
    op.create_index("ix_family_knowledge_key", "family_knowledge", ["family_id", "key"])

    op.create_table(
        "evidence_policy",
        _ulid_pk(),
        sa.Column("policy_type", sa.String(length=64), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("rule_text", sa.Text(), nullable=True),
        sa.Column("display_text", sa.Text(), nullable=True),
        sa.Column("hash", sa.String(length=128), nullable=False),
        _soft_delete(),
        *_timestamps(),
        sa.UniqueConstraint("policy_type", "region", "version", name="uq_evidence_policy_version"),
    )

    op.create_table(
        "sensor_event",
        _ulid_pk(),
        sa.Column("device_id", sa.String(length=26), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        _jsonb("payload"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
    )
    op.create_index("ix_sensor_event_device_id", "sensor_event", ["device_id"])
    op.create_index("ix_sensor_event_ts", "sensor_event", ["ts"])

    op.create_table(
        "camera_event",
        _ulid_pk(),
        sa.Column("camera_id", sa.String(length=26), nullable=False),
        sa.Column("session_id", sa.String(length=26), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("clip_path", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["camera_id"], ["device.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sleep_session.id"]),
    )
    op.create_index("ix_camera_event_camera_id", "camera_event", ["camera_id"])
    op.create_index("ix_camera_event_ts", "camera_event", ["ts"])

    op.create_table(
        "media_asset",
        _ulid_pk(),
        sa.Column("family_id", sa.String(length=26), nullable=False),
        sa.Column("baby_id", sa.String(length=26), nullable=True),
        sa.Column("event_id", sa.String(length=26), nullable=True),
        sa.Column("local_path", sa.Text(), nullable=False),
        sa.Column("thumbnail_path", sa.Text(), nullable=True),
        sa.Column("camera_id", sa.String(length=26), nullable=True),
        sa.Column("encrypted", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _jsonb("tags"),
        _jsonb("meta"),
        _soft_delete(),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
        sa.ForeignKeyConstraint(["baby_id"], ["baby.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["observation_event.event_id"]),
        sa.ForeignKeyConstraint(["camera_id"], ["device.id"]),
    )
    op.create_index("ix_media_asset_family_id", "media_asset", ["family_id"])
    op.create_index("ix_media_asset_baby_id", "media_asset", ["baby_id"])

    op.create_table(
        "audit_log",
        _ulid_pk(),
        sa.Column(
            "ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        _jsonb("actor"),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=False),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rule_version", sa.String(length=64), nullable=True),
        sa.Column("llm_call_id", sa.String(length=64), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "sync_state",
        sa.Column("client_id", sa.String(length=128), primary_key=True),
        sa.Column("family_id", sa.String(length=26), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pending_count", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
    )
    op.create_index("ix_sync_state_family_id", "sync_state", ["family_id"])

    _install_updated_at_triggers()
    _install_audit_immutability()


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trg_audit_log_no_update ON "audit_log";')
    op.execute('DROP TRIGGER IF EXISTS trg_audit_log_no_delete ON "audit_log";')
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation();")
    for table in reversed(UPDATED_AT_TABLES):
        op.execute(f'DROP TRIGGER IF EXISTS trg_{table}_updated_at ON "{table}";')
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

    for table in [
        "sync_state",
        "audit_log",
        "media_asset",
        "camera_event",
        "sensor_event",
        "evidence_policy",
        "family_knowledge",
        "sleep_session",
        "alert_delivery",
        "alert",
        "derived_baby_state",
        "mother_health",
        "solid_food_log",
        "growth_log",
        "milestone_log",
        "jaundice_photo",
        "symptom_event",
        "medication_log",
        "vaccine_record",
        "supplement_log",
        "temperature_log",
        "sleep_log",
        "diaper_log",
        "feeding_log",
        "observation_event",
        "baby",
        "device",
        "user",
        "family",
    ]:
        op.drop_table(table)
