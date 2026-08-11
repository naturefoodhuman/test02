# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/events.py —— ObservationEvent ORM（事件溯源核心）。
# 依据：ENGINEERING_DESIGN §5.1（ObservationEvent 数据契约 SSOT）、§6.1/§6.2；TASK_BACKLOG APC-T004。
# 设计：PK event_id（ULID）；idx(baby_id,event_type,start_time DESC)；
#       双状态字段 sync_status(pending|synced) + processing_status(raw|normalized|derived)；
#       correction_of 自引用（correction 链）；is_deleted 软删除；raw_input/normalized_payload jsonb。

"""ObservationEvent ORM（事件溯源核心，ENGINEERING_DESIGN §5.1 数据契约 SSOT）。

字段对齐 §5.1：
    event_id, baby_id, family_id, user_id, device_id, event_type,
    start_time, end_time, client_created_at, server_received_at,
    raw_input, normalized_payload, confidence, source, attachments,
    correction_of, is_deleted.

双状态字段（§6.2）：
    sync_status(pending|synced) — 同步状态（PowerSync 上行）。
    processing_status(raw|normalized|derived) — 处理状态（normalization 流水线）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TimestampMixin, ULIDPrimaryKey


class ObservationEvent(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """ObservationEvent（事件溯源核心，§5.1 数据契约 SSOT）。

    PK 为 event_id（ULID，应用层生成）；idx(baby_id,event_type,start_time DESC)。
    correction_of 自引用形成 correction 链（软删除旧事件 + 新事件指向旧 event_id）。
    """

    __tablename__ = "observation_event"

    # ULIDPrimaryKey 提供 id；此处别名 event_id 与 §5.1 契约对齐（同列）。
    # 注：SQLAlchemy 中 id 即为主键列，event_id 为同列别名通过 column_property 较重，
    # 此处直接用 id 作 event_id（应用层用 event_id 语义，DB 列名 id）。
    baby_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("baby.id", ondelete="RESTRICT"), nullable=False
    )
    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    server_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_input: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(default=1.0, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    attachments: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, default=list)
    correction_of: Mapped[str | None] = mapped_column(String(26), nullable=True)
    # 双状态字段（§6.2）：sync_status(pending|synced) 与 processing_status(pending|normalized|projected)。
    sync_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    processing_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    __table_args__ = (
        CheckConstraint(
            "source IN ('manual', 'voice_text', 'camera', 'sensor', 'ai', 'system')",
            name="ck_observation_event_source",
        ),
        CheckConstraint(
            "sync_status IN ('pending', 'synced')",
            name="ck_observation_event_sync_status",
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'normalized', 'projected')",
            name="ck_observation_event_processing_status",
        ),
        # §6.1 索引：idx(baby_id, event_type, start_time DESC)。
        Index(
            "ix_observation_event_baby_type_start",
            "baby_id",
            "event_type",
            text("start_time DESC"),
        ),
        Index("ix_observation_event_family_id", "family_id"),
        Index("ix_observation_event_correction_of", "correction_of"),
    )


__all__ = ["ObservationEvent"]
