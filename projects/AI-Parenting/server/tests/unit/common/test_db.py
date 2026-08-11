# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
"""SQLAlchemy async 数据访问基础设施单元测试（APC-T003）。

不连真实 DB：仅验证 engine/session factory 的构造、惰性、reset/dispose 行为。
连接参数来自 Settings.database（默认 dev URL）。
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from server.app import db
from server.app.settings import get_settings


@pytest.fixture(autouse=True)
def _reset_db_singleton():
    """每个用例前后重置 db 进程级单例，避免串扰。"""
    db.reset_db()
    yield
    db.reset_db()


def test_get_engine_is_lazy_and_singleton():
    """engine 惰性创建，且同进程内单例（同 Settings）。"""
    assert db._engine is None
    e1 = db.get_engine()
    assert isinstance(e1, AsyncEngine)
    e2 = db.get_engine()
    assert e1 is e2  # 单例


def test_get_session_factory_is_lazy_and_singleton():
    """session factory 惰性创建且单例。"""
    assert db._session_factory is None
    f1 = db.get_session_factory()
    assert isinstance(f1, async_sessionmaker)
    f2 = db.get_session_factory()
    assert f1 is f2


def test_reset_db_clears_singletons():
    """reset_db 后单例清空，下次重建为新实例。"""
    e1 = db.get_engine()
    db.reset_db()
    assert db._engine is None
    assert db._session_factory is None
    e2 = db.get_engine()
    assert e1 is not e2


def test_engine_uses_settings_database_url():
    """engine URL 来自 Settings.database.url。"""
    s = get_settings()
    e = db.get_engine(s)
    # SQLAlchemy 默认遮蔽密码为 ***，用 render_as_string 显式还原比对。
    assert e.url.render_as_string(hide_password=False) == s.database.url


def test_engine_pool_pre_ping_enabled():
    """pool_pre_ping=True，避免 DB 重启后死连接。"""
    e = db.get_engine()
    assert e.pool._pre_ping is True


@pytest.mark.asyncio
async def test_dispose_db_clears_and_disposes():
    """dispose_db 释放连接池并清空单例。"""
    db.get_engine()  # 触发惰性创建
    await db.dispose_db()
    assert db._engine is None
    assert db._session_factory is None
    # dispose 后再 dispose 不报错（幂等）。
    await db.dispose_db()
