# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/base.py —— ORM 基类与通用 mixin。
# 依据：ENGINEERING_DESIGN §5.1（ObservationEvent 数据契约：ULID event_id、is_deleted 软删除）、
#       §6（数据模型）；ARCHITECTURE_FINAL §6（M1 硬事实 PostgreSQL）；TASK_BACKLOG APC-T004。
# 设计：ULID 作 PK（应用层生成，26 字符 Crockford base32，与 common/ids.py 对齐）。
#       软删除（is_deleted）+ partial unique index；不物理删除。
#       created_at/updated_at：应用层写入；updated_at 另由 PG trigger 自动更新（迁移层）。
#       时区：DB 存 UTC timestamptz，ORM 用 timezone-aware datetime（与 common/clock.py 对齐）。

"""ORM 基类与通用 mixin。

- ``Base``：``DeclarativeBase``，所有模型共享，供 Alembic ``target_metadata``。
- ``ULIDPrimaryKey``：26 字符 ULID 主键（应用层生成，与 ``common/ids.py`` 对齐）。
- ``TimestampMixin``：``created_at``/``updated_at``（timezone-aware UTC）。
- ``SoftDeleteMixin``：``is_deleted`` 软删除标志（不物理删除，配合 partial index）。

时区：DB 列用 ``TIMESTAMP WITH TIME ZONE``（timestamptz），ORM 用 timezone-aware datetime，
与 ``common/clock.py`` 的 UTC 时钟对齐（架构 §22，领域层不出现 naive datetime）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类（共享 metadata，供 Alembic autogenerate）。"""


class ULIDPrimaryKey:
    """ULID 主键 mixin（26 字符 Crockford base32，应用层生成）。

    与 ``common/ids.new_id()`` 对齐；DB 不自动生成，写入前由应用层赋值。
    """

    id: Mapped[str] = mapped_column(String(26), primary_key=True)


class TimestampMixin:
    """创建/更新时间戳（timezone-aware UTC）。

    ``created_at``/``updated_at`` 由应用层写入（``Clock.now()``）；
    ``updated_at`` 另由 PG trigger 在 UPDATE 时自动刷新（见迁移 0001）。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SoftDeleteMixin:
    """软删除 mixin（``is_deleted`` 标志，不物理删除）。

    配合 partial unique index（``WHERE is_deleted = false``），允许同名实体在删除后重建。
    """

    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)


__all__ = ["Base", "SoftDeleteMixin", "TimestampMixin", "ULIDPrimaryKey"]
