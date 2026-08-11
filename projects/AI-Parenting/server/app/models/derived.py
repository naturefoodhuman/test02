# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/derived.py —— 派生状态与告警 ORM。
# 依据：ENGINEERING_DESIGN §6.1（derived_baby_state/alert/alert_delivery/sleep_session）；
#       §4.2（sensor_event/camera_event 传感器证据流）；TASK_BACKLOG APC-T004。
# 设计：derived_baby_state 以 baby_id 为 PK（upsert 当前快照）；alert 多级阈值 + ack 状态机；
#       alert_delivery 送达审计；sleep_session 睡眠会话状态机；sensor_event/camera_event 传感器原始证据。

"""派生状态与告警 ORM。

表结构 SSOT：``ENGINEERING_DESIGN §6.1`` + ``§4.2``（传感器证据流）。
- ``derived_baby_state``：baby_id PK + snapshot jsonb + computed_at（upsert 当前快照）。
- ``alert``：多级阈值（gray/blue/yellow/orange/red）+ ack 状态机。
- ``alert_delivery``：送达审计（channel/target/status/sent_at/receipt）。
- ``sleep_session``：睡眠会话状态机（state/started_at/ended_at/roi_config）。
- ``sensor_event``/``camera_event``：传感器/摄像头原始证据（MQTT/RTSP 入库）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TimestampMixin, ULIDPrimaryKey


class DerivedBabyState(Base, TimestampMixin):
    """派生宝宝状态（§6.1：baby_id PK + snapshot jsonb + computed_at，upsert 当前快照）。

    单行 per baby（baby_id 为主键），每次派生 upsert 覆盖当前快照。
    """

    __tablename__ = "derived_baby_state"

    baby_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("baby.id", ondelete="CASCADE"), primary_key=True
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Alert(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """告警（§6.1：level 多级阈值 + type + evidence jsonb + status + ack 状态机）。

    level：gray(灰)/blue/yellow/orange/red（医疗告警分级，架构 §11）。
    status：active/acked/resolved（告警状态机，通知编排器驱动）。
    """

    __tablename__ = "alert"

    baby_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("baby.id", ondelete="RESTRICT"), nullable=False
    )
    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    ack_by: Mapped[str | None] = mapped_column(String(26), nullable=True)
    ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "level IN ('gray', 'blue', 'yellow', 'orange', 'red')",
            name="ck_alert_level",
        ),
        CheckConstraint(
            "status IN ('active', 'acked', 'resolved')",
            name="ck_alert_status",
        ),
        Index("ix_alert_baby_status", "baby_id", "status"),
        Index("ix_alert_family_level", "family_id", "level"),
    )


class AlertDelivery(Base, ULIDPrimaryKey, TimestampMixin):
    """告警送达审计（§6.1：alert_id + channel + target + status + sent_at + receipt）。

    不可删除（审计要求，架构 §11/§15）；不继承 SoftDeleteMixin。
    """

    __tablename__ = "alert_delivery"

    alert_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    receipt: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'delivered', 'failed')",
            name="ck_alert_delivery_status",
        ),
        Index("ix_alert_delivery_alert_id", "alert_id"),
    )


class SleepSession(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """睡眠会话（§6.1：baby_id + state + started_at + ended_at + roi_config jsonb）。"""

    __tablename__ = "sleep_session"

    baby_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("baby.id", ondelete="RESTRICT"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    roi_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "state IN ('active', 'paused', 'ended')",
            name="ck_sleep_session_state",
        ),
        Index("ix_sleep_session_baby_started", "baby_id", "started_at"),
    )


class SensorEvent(Base, ULIDPrimaryKey, TimestampMixin):
    """传感器原始事件（§4.2：mmWave/雷达体征证据流，MQTT 入库）。

    不可删除（证据溯源）；不继承 SoftDeleteMixin。
    """

    __tablename__ = "sensor_event"

    baby_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    device_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_sensor_event_family_received", "family_id", "received_at"),
        Index("ix_sensor_event_device_id", "device_id"),
    )


class CameraEvent(Base, ULIDPrimaryKey, TimestampMixin):
    """摄像头事件（§4.2：RTSP/ISAPI 视频分析证据，事件片段索引）。

    不可删除（证据溯源）；不继承 SoftDeleteMixin。
    """

    __tablename__ = "camera_event"

    baby_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    device_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    clip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_camera_event_family_occurred", "family_id", "occurred_at"),
        Index("ix_camera_event_device_id", "device_id"),
    )


__all__ = [
    "Alert",
    "AlertDelivery",
    "CameraEvent",
    "DerivedBabyState",
    "SensorEvent",
    "SleepSession",
]
