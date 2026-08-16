# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-15 00:00:00
"""NormalizationWorker 集成测试（APC-T014，需 DB）。

验证端到端（真实 PG + SqlAlchemyWorkerContext）：
    - insert：worker.handle → 写 feeding_log + 推进 processing_status=normalized。
    - 重复 NOTIFY 去重：processing_status 已 normalized 时再次 handle 不重复写。
    - delete：worker.handle(op=delete) → 软删除派生行（is_deleted=true）。
    - 纠错链：correct 后旧 event_id 派生行被软删除，新事件派生行生效。
    - recover：recover_pending 扫描 pending 事件重新投递 → worker 补处理。

连 AI_parenting_dev 库；单 asyncio.run + _reset_db autouse（与 test_normalization 一致）。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select

from server.app import db as db_module
from server.app.common.clock import SystemClock
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.events.domain import Source, SyncStatus
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.event_worker import EventWorker
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family
from server.app.models.events import ObservationEvent as Orm
from server.app.models.logs import FeedingLog
from server.app.normalization.worker import NormalizationWorker

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 15, 8, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_db():
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_and_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="worker 测试家", timezone="Asia/Shanghai")
    session.add(family)
    await session.flush()
    baby = Baby(id=new_id(), family_id=family.id, birth_date=date(2026, 6, 1), sex="male")
    session.add(baby)
    await session.flush()
    return family.id, baby.id


async def _seed_event(
    session,
    family_id,
    baby_id,
    *,
    event_type="feeding",
    source=Source.MANUAL,
    payload=None,
    correction_of=None,
) -> str:
    svc = EventService(
        repository=SqlAlchemyObservationEventRepository(session),
        clock=SystemClock(),
        session=session,
    )
    if payload is None:
        payload = {"amount_ml": 120, "feeding_type": "bottle"}
    if correction_of is None:
        event_id = new_id()
        await svc.record(
            event_id=event_id,
            baby_id=baby_id,
            family_id=family_id,
            event_type=event_type,
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload=payload,
            source=source,
            sync_status=SyncStatus.SYNCED,
        )
        return event_id
    else:
        # correct 内部生成新 event_id；返回新事件。
        new_event = await svc.correct(
            correction_of=correction_of,
            baby_id=baby_id,
            family_id=family_id,
            event_type=event_type,
            start_time=NOW,
            client_created_at=NOW,
            normalized_payload=payload,
            source=source,
        )
        return new_event.event_id


def _worker() -> NormalizationWorker:
    return NormalizationWorker(session_factory=get_session_factory())


async def _active_feeding_logs(session, event_id) -> list[FeedingLog]:
    return (
        (await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id)))
        .scalars()
        .all()
    )


def test_worker_insert_normalizes_and_advances_status():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as seed_session:
            family_id, baby_id = await _make_family_and_baby(seed_session)
            event_id = await _seed_event(seed_session, family_id, baby_id)
            await seed_session.commit()
        # worker 用独立 session 处理。
        worker = _worker()
        await worker.handle({"event_id": event_id, "op": "insert"})
        # 读回验证。
        async with factory() as session:
            logs = await _active_feeding_logs(session, event_id)
            orm = (await session.execute(select(Orm).where(Orm.id == event_id))).scalar_one()
            return {
                "log_count": len(logs),
                "amount_ml": logs[0].amount_ml if logs else None,
                "processing_status": orm.processing_status,
            }

    r = asyncio.run(run())
    assert r["log_count"] == 1
    assert r["amount_ml"] == 120
    assert r["processing_status"] == "normalized"


def test_worker_dedup_repeated_notify_no_duplicate():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as seed_session:
            family_id, baby_id = await _make_family_and_baby(seed_session)
            event_id = await _seed_event(seed_session, family_id, baby_id)
            await seed_session.commit()
        worker = _worker()
        await worker.handle({"event_id": event_id, "op": "insert"})
        # 重复 NOTIFY（同一 event_id 再次投递）。
        await worker.handle({"event_id": event_id, "op": "insert"})
        async with factory() as session:
            logs = await _active_feeding_logs(session, event_id)
            return {"log_count": len(logs)}

    assert asyncio.run(run())["log_count"] == 1


def test_worker_delete_soft_deletes_log():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as seed_session:
            family_id, baby_id = await _make_family_and_baby(seed_session)
            event_id = await _seed_event(seed_session, family_id, baby_id)
            await seed_session.commit()
        worker = _worker()
        await worker.handle({"event_id": event_id, "op": "insert"})  # 先归一化写 log。
        await worker.handle({"event_id": event_id, "op": "delete"})  # 软删除派生行。
        async with factory() as session:
            all_logs = (
                (await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id)))
                .scalars()
                .all()
            )
            active = [lg for lg in all_logs if not lg.is_deleted]
            return {"total": len(all_logs), "active": len(active)}

    r = asyncio.run(run())
    assert r["total"] == 1  # 行仍在（不物理删除，§5.1）。
    assert r["active"] == 0  # 但 is_deleted=true。


def test_worker_correction_chain_soft_deletes_old_log():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as seed_session:
            family_id, baby_id = await _make_family_and_baby(seed_session)
            old_event_id = await _seed_event(seed_session, family_id, baby_id)
            await seed_session.commit()
        worker = _worker()
        # 先归一化旧事件 → 旧 feeding_log。
        await worker.handle({"event_id": old_event_id, "op": "insert"})
        # 纠正：correct 软删除旧事件 + 新事件 correction_of 指向旧 event_id（同 baby）。
        async with factory() as seed_session:
            new_event_id = await _seed_event(
                seed_session, family_id, baby_id, correction_of=old_event_id
            )
            await seed_session.commit()
        # worker 处理新事件：先软删除旧 event_id 派生行，再写新 feeding_log。
        await worker.handle({"event_id": new_event_id, "op": "insert"})
        async with factory() as session:
            old_logs = (
                (
                    await session.execute(
                        select(FeedingLog).where(FeedingLog.event_id == old_event_id)
                    )
                )
                .scalars()
                .all()
            )
            new_logs = (
                (
                    await session.execute(
                        select(FeedingLog).where(FeedingLog.event_id == new_event_id)
                    )
                )
                .scalars()
                .all()
            )
            return {
                "old_active": sum(1 for lg in old_logs if not lg.is_deleted),
                "new_active": sum(1 for lg in new_logs if not lg.is_deleted),
            }

    r = asyncio.run(run())
    assert r["old_active"] == 0  # 旧派生行已软删除（纠错链）。
    assert r["new_active"] == 1  # 新派生行生效。


def test_recover_pending_redelivers_pending_event():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as seed_session:
            family_id, baby_id = await _make_family_and_baby(seed_session)
            event_id = await _seed_event(seed_session, family_id, baby_id)
            await seed_session.commit()
        # 事件处于 pending（未归一化），模拟崩溃后 recover_pending 重新投递。
        # EventWorker.recover_pending 扫描 pending 事件，调 handler（worker.handle）。
        worker = _worker()
        from server.app.common.event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        event_worker = EventWorker(bus=bus, session_factory=get_session_factory())
        event_worker.add_handler(worker)
        count = await event_worker.recover_pending()
        async with factory() as session:
            logs = await _active_feeding_logs(session, event_id)
            orm = (await session.execute(select(Orm).where(Orm.id == event_id))).scalar_one()
            return {
                "recovered_count": count,
                "log_count": len(logs),
                "processing_status": orm.processing_status,
            }

    r = asyncio.run(run())
    assert r["recovered_count"] >= 1  # 扫描到至少 1 个 pending 事件。
    assert r["log_count"] == 1  # worker 补处理写了 feeding_log。
    assert r["processing_status"] == "normalized"
