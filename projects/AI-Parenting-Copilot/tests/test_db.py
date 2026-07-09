# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 23:35:00


"""APC-T003 tests for SQLAlchemy async DB helpers."""

from __future__ import annotations

import pytest

from server.app.common.errors import ConfigurationError
from server.app.db import create_optional_engine, normalize_database_url
from server.app.settings import Settings


def test_normalize_database_url_accepts_postgres_and_asyncpg() -> None:
    assert normalize_database_url("postgresql://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
    assert (
        normalize_database_url("postgresql+asyncpg://u:p@host/db")
        == "postgresql+asyncpg://u:p@host/db"
    )


def test_normalize_database_url_rejects_non_postgres() -> None:
    with pytest.raises(ConfigurationError):
        normalize_database_url("sqlite:///local.db")


def test_optional_engine_returns_none_in_dev_mode_without_database_url() -> None:
    settings = Settings(env="dev")
    settings.database.url = None

    assert create_optional_engine(settings) is None
