# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00


"""observation_event notify trigger

Revision ID: 0002_event_notify_trigger
Revises: 0001_initial_schema
Create Date: 2026-07-09 13:40:00 CST
"""

from __future__ import annotations

from alembic import op

revision = "0002_event_notify_trigger"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION notify_observation_event_changed()
        RETURNS TRIGGER AS $$
        DECLARE
            payload json;
        BEGIN
            payload = json_build_object(
                'event_id', COALESCE(NEW.event_id, OLD.event_id),
                'baby_id', COALESCE(NEW.baby_id, OLD.baby_id),
                'operation', TG_OP
            );
            PERFORM pg_notify('events.changed', payload::text);
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute('DROP TRIGGER IF EXISTS trg_observation_event_notify ON "observation_event";')
    op.execute(
        """
        CREATE TRIGGER trg_observation_event_notify
        AFTER INSERT OR UPDATE OR DELETE ON observation_event
        FOR EACH ROW EXECUTE FUNCTION notify_observation_event_changed();
        """
    )


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trg_observation_event_notify ON "observation_event";')
    op.execute("DROP FUNCTION IF EXISTS notify_observation_event_changed();")
