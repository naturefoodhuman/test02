# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""PG LISTEN/NOTIFY 事件总线集成测试（APC-T011，需 DB）。

连 AI_parenting_dev 库验证：
    - 插入 observation_event 后经 trigger 收到 NOTIFY events.changed（payload 含 event_id/baby_id/op）。
    - PgListenEventBus 订阅 events.changed，handler 收到 payload。
    - EventWorker.recover_pending 扫描 processing_status=pending 事件重新投递（崩溃恢复，§11）。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
每个测试用单一 asyncio.run（避免跨事件循环的 engine 死连接问题，与 test_audit 一致）。
observation_event 表有 FK 到 baby.id/family.id（RESTRICT），故先建真实 family+baby 行。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import pytest

from server.app import db as db_module
from server.app.common.clock import SystemClock
from server.app.common.event_bus import PgListenEventBus
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.events.domain import Source
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.event_worker import EventWorker
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family
from server.app.settings import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset_db():
    db_module.reset_db()
    yield
    db_module.reset_db()


def _dsn() -> str:
    """SQLAlchemy URL → asyncpg DSN（剥离 +asyncpg 前缀）。"""
    return get_settings().database.url.replace("postgresql+asyncpg://", "postgresql://")


async def _make_family_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="NOTIFY测试家", timezone="Asia/Shanghai")
    session.add(family)
    await session.flush()
    baby = Baby(id=new_id(), family_id=family.id, birth_date=date(2026, 6, 1), sex="male")
    session.add(baby)
    await session.flush()
    return family.id, baby.id


def test_insert_event_triggers_notify_received_by_pg_listen_bus():
    """端到端：插入 observation_event → trigger NOTIFY → PgListenEventBus handler 收到 payload。"""

    async def run() -> dict:
        factory = get_session_factory()
        # 1. 启动 PgListenEventBus 订阅 events.changed。
        bus = PgListenEventBus(_dsn())
        received: list[dict] = []

        async def handler(payload):
            received.append(payload)

        await bus.subscribe("events.changed", handler)
        await bus.start()
        try:
            # 2. 插入一条 observation_event（trigger 会 NOTIFY）。
            async with factory() as session:
                family_id, baby_id = await _make_family_baby(session)
                svc = EventService(
                    repository=SqlAlchemyObservationEventRepository(session),
                    clock=SystemClock(),
                    session=session,
                )
                event_id = new_id()
                await svc.record(
                    event_id=event_id,
                    baby_id=baby_id,
                    family_id=family_id,
                    event_type="feeding",
                    start_time=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                    client_created_at=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                    normalized_payload={"amount_ml": 120},
                    source=Source.MANUAL,
                )
                await session.commit()
            # 3. 等待 NOTIFY 投递（asyncpg notifies 队列异步）。
            for _ in range(20):
                await asyncio.sleep(0.05)
                if received:
                    break
        finally:
            await bus.stop()
        if not received:
            return {"received": False, "payload": None}
        p = received[0]
        return {
            "received": True,
            "event_id": p.get("event_id"),
            "baby_id": p.get("baby_id"),
            "op": p.get("op"),
        }

    r = asyncio.run(run())
    assert r["received"] is True, "插入后应收到 NOTIFY events.changed"
    assert r["event_id"] is not None
    assert r["baby_id"] is not None
    assert r["op"] in {"insert", "update", "delete"}


def test_event_worker_recover_pending_scans_pending_events():
    """崩溃恢复（§11）：recover_pending 扫描 processing_status=pending 事件重新投递。"""

    async def run() -> dict:
        factory = get_session_factory()
        # 1. 插入 2 条 pending 事件（不启动 LISTEN，模拟崩溃后残留）。
        async with factory() as session:
            family_id, baby_id = await _make_family_baby(session)
            svc = EventService(
                repository=SqlAlchemyObservationEventRepository(session),
                clock=SystemClock(),
                session=session,
            )
            e1 = new_id()
            e2 = new_id()
            for eid in (e1, e2):
                await svc.record(
                    event_id=eid,
                    baby_id=baby_id,
                    family_id=family_id,
                    event_type="feeding",
                    start_time=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                    client_created_at=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                    normalized_payload={},
                    source=Source.MANUAL,
                )
            await session.commit()
        # 2. EventWorker（用 InMemoryEventBus 占位，不启动 LISTEN）+ 注入 handler 计数。
        from server.app.common.event_bus import InMemoryEventBus

        worker = EventWorker(bus=InMemoryEventBus(), session_factory=factory)
        recovered: list[str] = []

        async def collect(payload):
            recovered.append(payload["event_id"])

        worker.add_handler(collect)
        # 3. recover_pending 扫描 pending 事件投递（DB 可能含其他测试残留，故断言 ≥2 且含本批）。
        count = await worker.recover_pending()
        return {"count": count, "recovered": recovered, "e1": e1, "e2": e2}

    r = asyncio.run(run())
    assert r["count"] >= 2, "应至少扫描到本批 2 条 pending 事件"
    assert r["e1"] in r["recovered"], "本批 e1 应被重新投递"
    assert r["e2"] in r["recovered"], "本批 e2 应被重新投递"
