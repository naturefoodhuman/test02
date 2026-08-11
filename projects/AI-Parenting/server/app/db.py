# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/db.py —— SQLAlchemy async 数据访问基础设施。
# 依据：ENGINEERING_DESIGN §4（服务边界：Server↔Postgres 走 SQLAlchemy async + Alembic）、
#       §7（存储架构）；ARCHITECTURE_FINAL §7（PostgreSQL 权威源）；TASK_BACKLOG APC-T003。
# 设计：async engine + async_sessionmaker；URL/pool 来自 Settings.database。
#       写入统一走 Repository（架构 §4），本模块只提供会话工厂，不含业务逻辑。
#       dev/mock：未配置 DB 时应用仍可启动（不强制连 DB），engine 惰性创建。

"""SQLAlchemy async 数据访问基础设施。

提供进程级 async engine 与 async session factory（``async_sessionmaker``）。
URL 与连接池参数来自 ``Settings.database``（``PARENTING_DATABASE__*``）。
写入统一走 Repository（架构 §4），本模块只提供会话工厂，不含业务逻辑。

dev/mock 模式：未配置 DB 时应用仍可启动（APC-T002 验收），engine 惰性创建——
首次获取会话时才尝试连接，未连 DB 的测试/启动路径不触发连接。
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .settings import DatabaseSettings, Settings, get_settings

# ---- 进程级单例（惰性）----
# 测试通过 reset_db() 重置；prod 与 dev 共用同一 engine（连接池复用）。
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine(settings: DatabaseSettings) -> AsyncEngine:
    """按 DatabaseSettings 构造 async engine。

    ``pool_pre_ping=True``：每次借出连接前 ping，避免 DB 重启后拿到死连接。
    ``echo``：dev 调试 SQL 回显（默认 False）。
    """
    return create_async_engine(
        settings.url,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_pre_ping=True,
        future=True,
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """获取进程级 async engine（惰性初始化）。"""
    global _engine
    if _engine is None:
        s = settings or get_settings()
        _engine = _build_engine(s.database)
    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """获取进程级 async session factory（惰性初始化）。"""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(settings)
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_session(settings: Settings | None = None) -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：按请求提供 async session，自动关闭。

    用法（路由）::

        async def handler(session: AsyncSession = Depends(get_session)):
            ...
    """
    factory = get_session_factory(settings)
    async with factory() as session:
        yield session


def reset_db() -> None:
    """重置进程级 engine 与 session factory（测试用）。

    已创建的 engine 不主动 dispose（测试进程退出即清理）；调用本函数后，
    下次 ``get_engine`` / ``get_session_factory`` 按新 Settings 重建。
    """
    global _engine, _session_factory
    _engine = None
    _session_factory = None


async def dispose_db() -> None:
    """显式释放 engine 连接池（应用 shutdown / 测试 teardown 用）。"""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


__all__ = [
    "dispose_db",
    "get_engine",
    "get_session",
    "get_session_factory",
    "reset_db",
]
