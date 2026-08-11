# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# migrations/env.py —— Alembic 迁移环境（async）。
# 依据：ENGINEERING_DESIGN §4（Server↔Postgres 走 SQLAlchemy async + Alembic）、§7（存储）；
#       ARCHITECTURE_FINAL §7（PostgreSQL 权威源）；TASK_BACKLOG APC-T003。
# 设计：URL 从 Settings.database 读取（PARENTING_DATABASE__URL），不硬编码。
#       async 迁移：run_migrations_online 用 async engine 执行。
#       离线模式：alembic upgrade head --sql 生成 SQL 脚本（不连 DB）。

"""Alembic 迁移环境（async）。

URL 从 ``Settings.database`` 读取（``PARENTING_DATABASE__URL``），不硬编码。
在线迁移用 async engine 执行；离线模式（``--sql``）生成 SQL 脚本不连 DB。

Meta 集中在 ``server/app/db_meta.py``（待 APC-T004 起填充各领域 ORM 模型后聚合），
当前为空 Base，确保 ``alembic upgrade head`` 可在无表状态下运行。
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from server.app.models import Base
from server.app.settings import get_settings

# Alembic 配置对象（来自 alembic.ini）。
config = context.config

# 日志配置（alembic.ini [loggers] 等）。
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Settings 提供数据库 URL（PARENTING_DATABASE__URL）。
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.url)

# 目标 Meta：APC-T004 起聚合各领域 ORM 模型的 Base.metadata。
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本，不连 DB。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在已有连接上执行迁移。"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在线模式：用 async engine 执行迁移。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
