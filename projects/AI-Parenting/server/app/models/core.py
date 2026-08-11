# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/core.py —— 核心实体 ORM（family/user/device/baby）。
# 依据：ENGINEERING_DESIGN §6.1（核心实体与表）；ARCHITECTURE_FINAL §6/§7；TASK_BACKLOG APC-T004。
# 设计：ULID PK；family_id FK 贯穿；baby 预留多 baby（family_id FK）；
#       device.kind 枚举（phone/camera/mmwave/mac）；allergies jsonb；timezone 存 IANA 名。

"""核心实体 ORM：family / user / device / baby。

表结构 SSOT：``ENGINEERING_DESIGN §6.1``。
- ``family``：家庭（id, name, timezone）。
- ``user``：家庭成员（id, family_id FK, role, display_name, auth_hash）。
- ``device``：设备（id, family_id FK, kind 枚举, fcm_token, meta jsonb）。
- ``baby``：宝宝（id, family_id FK, 出生信息, 体重, 性别, 接种地区, allergies jsonb）。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TimestampMixin, ULIDPrimaryKey


class Family(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """家庭（架构 §6，多 baby 共享一个 family）。"""

    __tablename__ = "family"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # IANA 时区名（如 Asia/Shanghai），与 clock.py 的 UTC 时钟配合用于本地展示。
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Shanghai")

    __table_args__ = (
        # 软删除后允许同名家庭重建。
        Index("ix_family_name", "name", unique=False, postgresql_where=text("is_deleted = false")),
    )


class User(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """家庭成员（§6.1：role/display_name/auth_hash）。"""

    __tablename__ = "user"

    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 认证哈希（不存明文密码；auth_hash 由 auth 模块生成）。
    auth_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (Index("ix_user_family_id", "family_id"),)


class Device(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """设备（§6.1：kind 枚举 phone/camera/mmwave/mac，fcm_token，meta jsonb）。"""

    __tablename__ = "device"

    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    fcm_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "kind IN ('phone', 'camera', 'mmwave', 'mac')",
            name="ck_device_kind",
        ),
        Index("ix_device_family_id", "family_id"),
    )


class Baby(Base, ULIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """宝宝（§6.1：出生信息 + 体重 + 性别 + 接种地区 + allergies jsonb；预留多 baby）。"""

    __tablename__ = "baby"

    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="RESTRICT"), nullable=False
    )
    birth_date: Mapped[date] = mapped_column(nullable=False)
    gestational_age_weeks: Mapped[int | None] = mapped_column(nullable=True)
    is_preterm: Mapped[bool] = mapped_column(default=False, nullable=False)
    birth_weight_g: Mapped[int | None] = mapped_column(nullable=True)
    current_weight_g: Mapped[int | None] = mapped_column(nullable=True)
    current_weight_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sex: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # 接种地区（默认 CN），用于疫苗规则匹配。
    vaccine_region: Mapped[str] = mapped_column(String(8), nullable=False, default="CN")
    allergies: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("sex IN ('male', 'female')", name="ck_baby_sex"),
        Index("ix_baby_family_id", "family_id"),
    )


__all__ = ["Baby", "Device", "Family", "User"]
