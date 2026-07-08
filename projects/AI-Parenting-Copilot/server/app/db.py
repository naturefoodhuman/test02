# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 23:35:00


"""Database engine/session primitives for PostgreSQL + Alembic.

APC-T003 introduces the SQLAlchemy async infrastructure only. Domain models and
migrations are added by APC-T004 and later tasks.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from server.app.common.errors import ConfigurationError
from server.app.settings import DatabaseSettings, Settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative metadata root used by Alembic."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def normalize_database_url(url: str) -> str:
    """Normalize PostgreSQL URLs to SQLAlchemy asyncpg URLs."""

    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    raise ConfigurationError(
        "Database URL must use postgresql:// or postgresql+asyncpg://",
        evidence={"url_scheme": url.split(":", 1)[0] if ":" in url else "unknown"},
    )


def create_engine(database: DatabaseSettings) -> AsyncEngine:
    """Create an async SQLAlchemy engine from settings."""

    if not database.url:
        raise ConfigurationError("Database URL is not configured")
    return create_async_engine(
        normalize_database_url(database.url),
        echo=database.echo,
        pool_size=database.pool_size,
        max_overflow=database.max_overflow,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for repositories."""

    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide a transaction scope around repository operations."""

    async with session_factory() as session:
        async with session.begin():
            yield session


def create_optional_engine(settings: Settings) -> AsyncEngine | None:
    """Return None in dev/mock mode when DB is intentionally not configured."""

    if not settings.database.url:
        if settings.is_dev_mode:
            return None
        raise ConfigurationError("Database URL is required outside dev/test")
    return create_engine(settings.database)
