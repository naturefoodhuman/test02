# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""audit_log append-only trigger (BEFORE UPDATE/DELETE raise)

Revision ID: 0003_audit_append_trigger
Revises: 0002_timestamps_tz
Create Date: 2026-08-11 00:00:00

T004 修正：0001 迁移用 ``REVOKE UPDATE, DELETE ON audit_log FROM parenting`` 强制 append-only，
但 ``parenting`` 是 ``audit_log`` 的 owner（建表者），PG 中 owner 隐式持有所有权限，
``REVOKE`` 无法撤销 owner 的隐式权限——故 UPDATE/DELETE 仍可执行（集成测试证实）。

本迁移挂 BEFORE UPDATE/DELETE trigger，对任何 UPDATE/DELETE 抛异常，强制 append-only
（不依赖权限模型，owner 也无法绕过）。这是 PG append-only 的标准做法（§22.2）。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_audit_append_trigger"
down_revision: str | Sequence[str] | None = "0002_timestamps_tz"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_TRIGGER_FN_SQL = """
CREATE OR REPLACE FUNCTION parenting_audit_log_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (§22.2): % not allowed on row id=%',
        TG_OP, OLD.id;
END;
$$;
"""

_TRIGGER_SQL = (
    "CREATE TRIGGER audit_log_append_only "
    "BEFORE UPDATE OR DELETE ON audit_log "
    "FOR EACH ROW EXECUTE FUNCTION parenting_audit_log_append_only();"
)


def upgrade() -> None:
    """挂 append-only trigger：BEFORE UPDATE/DELETE 抛异常。"""
    bind = op.get_bind()
    bind.execute(sa.text(_TRIGGER_FN_SQL))
    bind.execute(sa.text(_TRIGGER_SQL))


def downgrade() -> None:
    """移除 append-only trigger。"""
    bind = op.get_bind()
    bind.execute(sa.text("DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log;"))
    bind.execute(sa.text("DROP FUNCTION IF EXISTS parenting_audit_log_append_only();"))
