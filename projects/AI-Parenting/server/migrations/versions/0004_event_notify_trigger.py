# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""observation_event NOTIFY trigger (events.changed channel)

Revision ID: 0004_event_notify_trigger
Revises: 0003_audit_append_trigger
Create Date: 2026-08-11 00:00:00

APC-T011：``observation_event`` AFTER INSERT/UPDATE/DELETE 触发 ``pg_notify('events.changed', ...)``，
payload 为 JSON（event_id/baby_id/family_id/op），供 Normalization worker 经 PG LISTEN 消费
（架构 §7.1：NOTIFY events.changed --> Normalization worker；§11 at-least-once + 幂等消费）。

设计要点：
    - AFTER trigger：确保行已落库，worker 可按 event_id 回查（崩溃恢复用 processing_status）。
    - payload 含 ``op``（INSERT/UPDATE/DELETE）、``event_id``、``baby_id``、``family_id``，
      满足 TASK_BACKLOG APC-T011（payload 包含 event_id、baby_id、operation）。
    - DELETE 时 ``NEW`` 为空，用 ``OLD`` 取字段；``op=DELETE`` 时 worker 不再归一化但需更新派生。
    - 用 ``pg_notify`` 而非 ``NOTIFY`` 语句，以便携带 JSON payload（原生 NOTIFY 只支持字符串）。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_event_notify_trigger"
down_revision: str | Sequence[str] | None = "0003_audit_append_trigger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_TRIGGER_FN_SQL = """
CREATE OR REPLACE FUNCTION parenting_event_notify() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    p json;
    eid varchar(26);
    bid varchar(26);
    fid varchar(26);
BEGIN
    IF TG_OP = 'DELETE' THEN
        eid := OLD.id; bid := OLD.baby_id; fid := OLD.family_id;
    ELSE
        eid := NEW.id; bid := NEW.baby_id; fid := NEW.family_id;
    END IF;
    p := json_build_object(
        'event_id', eid,
        'baby_id', bid,
        'family_id', fid,
        'op', lower(TG_OP)
    );
    PERFORM pg_notify('events.changed', p::text);
    RETURN NULL;
END;
$$;
"""

_TRIGGER_SQL = (
    "CREATE TRIGGER observation_event_notify "
    "AFTER INSERT OR UPDATE OR DELETE ON observation_event "
    "FOR EACH ROW EXECUTE FUNCTION parenting_event_notify();"
)


def upgrade() -> None:
    """挂 observation_event AFTER INSERT/UPDATE/DELETE NOTIFY trigger。"""
    bind = op.get_bind()
    bind.execute(sa.text(_TRIGGER_FN_SQL))
    bind.execute(sa.text(_TRIGGER_SQL))


def downgrade() -> None:
    """移除 NOTIFY trigger 与函数。"""
    bind = op.get_bind()
    bind.execute(sa.text("DROP TRIGGER IF EXISTS observation_event_notify ON observation_event;"))
    bind.execute(sa.text("DROP FUNCTION IF EXISTS parenting_event_notify();"))
