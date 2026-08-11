# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
"""初始迁移应用集成测试（APC-T004，需 DB）。

连 AI_parenting_dev 库验证：迁移已应用、28 表存在、updated_at trigger 挂载、
audit_log append-only（REVOKE UPDATE/DELETE）。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from server.app import db as db_module
from server.app.db import dispose_db, get_engine

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _reset_db():
    await db_module.dispose_db()
    yield
    await db_module.dispose_db()


def test_migration_applied_all_tables_exist():
    """迁移应用后 28 张业务表存在（§6.1）。"""
    import asyncio

    async def run():
        e = get_engine()
        async with e.connect() as c:
            r = await c.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                    "AND tablename != 'alembic_version' ORDER BY tablename"
                )
            )
            tables = {row[0] for row in r.fetchall()}
        await dispose_db()
        return tables

    tables = asyncio.run(run())
    expected = {
        "family",
        "user",
        "device",
        "baby",
        "observation_event",
        "feeding_log",
        "diaper_log",
        "sleep_log",
        "temperature_log",
        "supplement_log",
        "vaccine_record",
        "medication_log",
        "symptom_event",
        "jaundice_photo",
        "milestone_log",
        "growth_log",
        "solid_food_log",
        "media_asset",
        "derived_baby_state",
        "alert",
        "alert_delivery",
        "sleep_session",
        "sensor_event",
        "camera_event",
        "family_knowledge",
        "evidence_policy",
        "audit_log",
        "sync_state",
    }
    assert expected <= tables, f"missing tables: {expected - tables}"


def test_updated_at_triggers_attached():
    """26 张含 updated_at 的表挂了 trigger（§6.2）。"""
    import asyncio

    async def run():
        e = get_engine()
        async with e.connect() as c:
            r = await c.execute(
                text("SELECT count(*) FROM pg_trigger WHERE tgname LIKE 'trg_%_updated_at'")
            )
            count = r.fetchone()[0]
        await dispose_db()
        return count

    assert asyncio.run(run()) == 26


def test_audit_log_is_append_only():
    """audit_log append-only（§22.2）：权限层 REVOKE + trigger 层 BEFORE UPDATE/DELETE 抛异常。

    权限层（0001 REVOKE）对 owner 无效（parenting 是 audit_log owner，隐式持全权限），
    故 0003 迁移挂了 BEFORE UPDATE/DELETE trigger 强制 append-only（owner 也无法绕过）。
    本测试验证两层防护都在：权限层无 UPDATE/DELETE 授予，trigger 存在。
    """
    import asyncio

    async def run():
        e = get_engine()
        async with e.connect() as c:
            r = await c.execute(
                text(
                    "SELECT privilege_type FROM information_schema.role_table_grants "
                    "WHERE table_name='audit_log' AND grantee='parenting'"
                )
            )
            privs = {row[0] for row in r.fetchall()}
            r2 = await c.execute(
                text("SELECT count(*) FROM pg_trigger WHERE tgname = 'audit_log_append_only'")
            )
            trigger_count = r2.scalar()
        await dispose_db()
        return privs, trigger_count

    privs, trigger_count = asyncio.run(run())
    # 权限层：parenting 无 UPDATE/DELETE 授予（REVOKE 生效于显式授予，owner 隐式权限另算）。
    assert "UPDATE" not in privs
    assert "DELETE" not in privs
    assert "INSERT" in privs
    assert "SELECT" in privs
    # trigger 层：BEFORE UPDATE/DELETE trigger 存在（0003 迁移挂载，owner 也无法绕过）。
    assert trigger_count == 1


def test_timestamps_are_timestamptz():
    """所有时间戳列应为 TIMESTAMPTZ（架构 SSOT：models/base.py 文档 + §6.1）。

    0002 迁移把 0001 的 naive DateTime 列 ALTER 为 timestamptz。
    抽样验证 audit_log.ts 与 observation_event.start_time。
    """
    import asyncio

    async def run():
        e = get_engine()
        async with e.connect() as c:
            r = await c.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name='audit_log' AND column_name='ts'"
                )
            )
            audit_ts_type = r.scalar()
            r2 = await c.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name='observation_event' AND column_name='start_time'"
                )
            )
            obs_start_type = r2.scalar()
        await dispose_db()
        return audit_ts_type, obs_start_type

    audit_ts_type, obs_start_type = asyncio.run(run())
    assert audit_ts_type == "timestamp with time zone"
    assert obs_start_type == "timestamp with time zone"


def test_alembic_version_recorded():
    """alembic_version 表记录了初始迁移版本。"""
    import asyncio

    async def run():
        e = get_engine()
        async with e.connect() as c:
            r = await c.execute(text("SELECT version_num FROM alembic_version"))
            row = r.fetchone()
        await dispose_db()
        return row

    row = asyncio.run(run())
    assert row is not None
    assert len(row[0]) > 0
