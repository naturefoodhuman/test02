# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""normalize naive timestamp columns to timestamptz

Revision ID: 0002_timestamps_tz
Revises: 9dc5086c5ca6
Create Date: 2026-08-11 00:00:00

T004 修正：初始迁移中部分时间戳列用 ``sa.DateTime()``（无时区），
与架构 SSOT（§6.1 + models/base.py 文档"DB 列用 TIMESTAMP WITH TIME ZONE"）不一致。
本迁移把所有无时区时间戳列 ALTER 为 ``TIMESTAMPTZ``，统一 timezone-aware UTC。

涉及列（表.列）：
    audit_log.ts
    evidence_policy.effective_from / effective_to
    sync_state.last_seen_at
    baby.current_weight_at
    camera_event.occurred_at
    sensor_event.received_at
    alert.ack_at
    derived_baby_state.computed_at
    observation_event.start_time / end_time / client_created_at / server_received_at
    sleep_session.started_at / ended_at
    alert_delivery.sent_at
    feeding_log.started_at / ended_at

USING 子句：原 naive 列存的是应用层写入的 UTC（Clock.now() 返回 timezone-aware，
asyncpg 写 naive 列时丢时区信息但值仍是 UTC），故 ``USING col AT TIME ZONE 'UTC'``
把 naive UTC 解释为 timestamptz，不偏移。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_timestamps_tz"
down_revision: str | Sequence[str] | None = "9dc5086c5ca6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (table, column) 清单——所有原 naive DateTime 列。
_TZ_COLUMNS: list[tuple[str, str]] = [
    ("audit_log", "ts"),
    ("evidence_policy", "effective_from"),
    ("evidence_policy", "effective_to"),
    ("sync_state", "last_seen_at"),
    ("baby", "current_weight_at"),
    ("camera_event", "occurred_at"),
    ("sensor_event", "received_at"),
    ("alert", "ack_at"),
    ("derived_baby_state", "computed_at"),
    ("observation_event", "start_time"),
    ("observation_event", "end_time"),
    ("observation_event", "client_created_at"),
    ("observation_event", "server_received_at"),
    ("sleep_session", "started_at"),
    ("sleep_session", "ended_at"),
    ("alert_delivery", "sent_at"),
    ("feeding_log", "started_at"),
    ("feeding_log", "ended_at"),
]


def upgrade() -> None:
    """把所有 naive timestamp 列 ALTER 为 TIMESTAMPTZ（架构 SSOT 要求）。"""
    bind = op.get_bind()
    for table, column in _TZ_COLUMNS:
        # 原列存的是 UTC（应用层 Clock.now() 写入），USING ... AT TIME ZONE 'UTC'
        # 把 naive UTC 解释为 timestamptz，不偏移。
        bind.execute(
            sa.text(
                f'ALTER TABLE {table} ALTER COLUMN "{column}" '
                f"TYPE TIMESTAMPTZ USING \"{column}\" AT TIME ZONE 'UTC'"
            )
        )


def downgrade() -> None:
    """回退：TIMESTAMPTZ → TIMESTAMP WITHOUT TIME ZONE（丢时区，值仍为 UTC）。"""
    bind = op.get_bind()
    for table, column in _TZ_COLUMNS:
        bind.execute(
            sa.text(
                f'ALTER TABLE {table} ALTER COLUMN "{column}" '
                f"TYPE TIMESTAMP WITHOUT TIME ZONE USING \"{column}\" AT TIME ZONE 'UTC'"
            )
        )
