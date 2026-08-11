# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/logs.py —— 各领域派生日志表（normalization 生成，event_id FK 溯源）。
# 依据：ENGINEERING_DESIGN §6.1（各 *_log 含 event_id FK 溯源）、§5.1（ObservationEvent 契约）；
#       FINAL_PRD §7.3（payload jsonb）；TASK_BACKLOG APC-T004。
# 设计：各 log 表 = event_id FK 溯源 + baby_id + 业务字段（jsonb payload 或结构化列）。
#       T004 初版：feeding_log 给结构化列（P0 端到端），其余 log 最小化（event_id + payload jsonb），
#       具体结构化列留待各领域任务（feeding/diaper/sleep/...）细化。

"""各领域派生日志表（normalization 生成，event_id FK 溯源）。

表结构 SSOT：``ENGINEERING_DESIGN §6.1``（各 *_log 含 event_id FK 溯源）。
PRD §7.3 的 payload 为 jsonb；T004 初版各 log 表用最小结构，
feeding_log 额外给 P0 端到端所需的结构化列，其余 log 的结构化列留待各领域任务细化。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TimestampMixin, ULIDPrimaryKey


class _LogBase:
    """各 log 表共享列：event_id FK 溯源 + baby_id + payload jsonb。

    event_id 指向 observation_event.id（normalization 从 event 派生 log）。
    """

    event_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("observation_event.id", ondelete="RESTRICT"),
        nullable=False,
    )
    baby_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("baby.id", ondelete="RESTRICT"), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class FeedingLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """喂养日志（P0 端到端核心，结构化列 + payload jsonb 兜底）。

    结构化列用于 P0 端到端查询（24h 奶量、距上次喂奶）；其余扩展字段入 payload jsonb。
    """

    __tablename__ = "feeding_log"

    amount_ml: Mapped[int | None] = mapped_column(nullable=True)
    feeding_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_feeding_log_baby_started", "baby_id", "started_at"),)


class DiaperLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """尿布日志（§6.1，最小结构；具体字段待领域任务细化入 payload）。"""

    __tablename__ = "diaper_log"

    __table_args__ = (Index("ix_diaper_log_baby_id", "baby_id"),)


class SleepLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """睡眠日志（§6.1，最小结构）。"""

    __tablename__ = "sleep_log"

    __table_args__ = (Index("ix_sleep_log_baby_id", "baby_id"),)


class TemperatureLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """体温日志（§6.1，最小结构）。"""

    __tablename__ = "temperature_log"

    __table_args__ = (Index("ix_temperature_log_baby_id", "baby_id"),)


class SupplementLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """补剂日志（§6.1，最小结构）。"""

    __tablename__ = "supplement_log"

    __table_args__ = (Index("ix_supplement_log_baby_id", "baby_id"),)


class VaccineRecord(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """疫苗记录（§6.1，最小结构）。"""

    __tablename__ = "vaccine_record"

    __table_args__ = (Index("ix_vaccine_record_baby_id", "baby_id"),)


class MedicationLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """用药日志（§6.1，最小结构）。"""

    __tablename__ = "medication_log"

    __table_args__ = (Index("ix_medication_log_baby_id", "baby_id"),)


class SymptomEvent(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """症状事件（§6.1，最小结构）。"""

    __tablename__ = "symptom_event"

    __table_args__ = (Index("ix_symptom_event_baby_id", "baby_id"),)


class JaundicePhoto(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """黄疸照片记录（§6.1，最小结构）。"""

    __tablename__ = "jaundice_photo"

    __table_args__ = (Index("ix_jaundice_photo_baby_id", "baby_id"),)


class MilestoneLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """发育里程碑日志（§6.1，最小结构）。"""

    __tablename__ = "milestone_log"

    __table_args__ = (Index("ix_milestone_log_baby_id", "baby_id"),)


class GrowthLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """生长记录（§6.1，最小结构；体重百分位派生）。"""

    __tablename__ = "growth_log"

    __table_args__ = (Index("ix_growth_log_baby_id", "baby_id"),)


class SolidFoodLog(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """辅食日志（§6.1 结构预留 V2/V3/V4，最小结构）。"""

    __tablename__ = "solid_food_log"

    __table_args__ = (Index("ix_solid_food_log_baby_id", "baby_id"),)


class MediaAsset(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin, _LogBase):
    """媒体资产元数据（§6.1；大文件不入库，仅存元数据与路径，架构 §7）。"""

    __tablename__ = "media_asset"

    asset_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_media_asset_baby_id", "baby_id"),
        Index("ix_media_asset_event_id", "event_id"),
    )


__all__ = [
    "DiaperLog",
    "FeedingLog",
    "GrowthLog",
    "JaundicePhoto",
    "MediaAsset",
    "MedicationLog",
    "MilestoneLog",
    "SleepLog",
    "SolidFoodLog",
    "SupplementLog",
    "SymptomEvent",
    "TemperatureLog",
    "VaccineRecord",
]
