# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""Event → Normalization → State 端到端集成测试（APC-T017，需 DB）。

验证服务端记录链路自动完成（架构 §4.1 / §7.1）：
    1. feeding event 写入 → worker.handle(insert) → 归一化写 feeding_log + 推进 normalized
       + 触发 State Engine 重算 → derived_baby_state 含 24h 奶量。
    2. soft delete → worker.handle(delete) → 软删除派生行 + 触发重算 → snapshot 更新（奶量 0）。
    3. 纠错链：correct 后旧派生行软删除 + 新事件归一化 + 重算 → snapshot 反映新值。

不 mock DB；worker 手动驱动（不后台跑 PG LISTEN，避免 flaky）。连 AI_parenting_dev 库。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from server.app import db as db_module
from server.app.common.clock import FixedClock
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.events.domain import Source, SyncStatus
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family
from server.app.models.derived import DerivedBabyState as DerivedOrm
from server.app.models.events import ObservationEvent as Orm
from server.app.models.logs import FeedingLog
from server.app.normalization.worker import NormalizationWorker
from server.app.state_engine.engine import StateEngine
from server.app.state_engine.infra import SqlAlchemyEventLoader
from server.app.state_engine.snapshot_repo import SqlAlchemySnapshotRepository

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 16, 8, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_db():
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_and_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="pipeline 测试家", timezone="Asia/Shanghai")
    session.add(family)
    await session.flush()
    baby = Baby(id=new_id(), family_id=family.id, birth_date=date(2026, 6, 1), sex="male")
    session.add(baby)
    await session.flush()
    return family.id, baby.id


async def _seed_pending_event(session, family_id, baby_id, *, payload, start) -> str:
    """写入 pending 事件（未归一化），返回 event_id。"""
    event_id = new_id()
    svc = EventService(
        repository=SqlAlchemyObservationEventRepository(session),
        clock=FixedClock(start),
        session=session,
    )
    await svc.record(
        event_id=event_id,
        baby_id=baby_id,
        family_id=family_id,
        event_type="feeding",
        start_time=start,
        client_created_at=start,
        normalized_payload=payload,
        source=Source.MANUAL,
        sync_status=SyncStatus.SYNCED,
    )
    return event_id


def _make_worker() -> NormalizationWorker:
    """构造端到端 worker：归一化后触发 StateEngine 重算（与 main 装配一致）。"""

    async def _state_recompute(baby_id: str) -> None:
        factory = get_session_factory()
        async with factory() as session:
            engine = StateEngine(
                event_loader=SqlAlchemyEventLoader(session),
                snapshot_repo=SqlAlchemySnapshotRepository(session),
                event_repo=SqlAlchemyObservationEventRepository(session),
                clock=FixedClock(NOW),
            )
            await engine.recompute(baby_id)
            await session.commit()

    return NormalizationWorker(
        session_factory=get_session_factory(),
        state_recompute=_state_recompute,
    )


def test_pipeline_feeding_event_to_derived_state():
    async def run() -> dict:
        factory = get_session_factory()
        start = NOW - timedelta(hours=1)
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_pending_event(
                session, family_id, baby_id, payload={"amount_ml": 150}, start=start
            )
            await session.commit()
        # 手动驱动 worker（模拟 events.changed NOTIFY）。
        worker = _make_worker()
        await worker.handle({"event_id": event_id, "baby_id": baby_id, "op": "insert"})
        # 读回验证：feeding_log + derived_baby_state + processing_status。
        async with factory() as session:
            logs = (
                await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id))
            ).scalars().all()
            snap = (
                await session.execute(select(DerivedOrm).where(DerivedOrm.baby_id == baby_id))
            ).scalar_one_or_none()
            ev = (
                await session.execute(select(Orm).where(Orm.id == event_id))
            ).scalar_one()
            return {
                "log_count": len(logs),
                "log_amount": logs[0].amount_ml if logs else None,
                "has_snapshot": snap is not None,
                "volume_24h": snap.snapshot["feeding"]["volume_ml_24h"] if snap else None,
                "processing_status": ev.processing_status,
            }

    r = asyncio.run(run())
    assert r["log_count"] == 1  # feeding_log 写入。
    assert r["log_amount"] == 150
    assert r["has_snapshot"] is True  # derived_baby_state 写入。
    assert r["volume_24h"] == 150.0  # 24h 奶量。
    assert r["processing_status"] == "projected"  # pending→normalized→projected。


def test_pipeline_soft_delete_updates_snapshot():
    async def run() -> dict:
        factory = get_session_factory()
        start = NOW - timedelta(hours=1)
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_pending_event(
                session, family_id, baby_id, payload={"amount_ml": 120}, start=start
            )
            await session.commit()
        worker = _make_worker()
        # 先归一化 → snapshot 含 120。
        await worker.handle({"event_id": event_id, "baby_id": baby_id, "op": "insert"})
        # 软删除事件（EventService.soft_delete）。
        async with factory() as session:
            svc = EventService(
                repository=SqlAlchemyObservationEventRepository(session),
                clock=FixedClock(NOW),
                session=session,
            )
            await svc.soft_delete(event_id=event_id)
            await session.commit()
        # worker 处理 delete NOTIFY → 软删除派生行 + 重算 → snapshot 奶量 0。
        await worker.handle({"event_id": event_id, "baby_id": baby_id, "op": "delete"})
        async with factory() as session:
            all_logs = (
                await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id))
            ).scalars().all()
            active_logs = [lg for lg in all_logs if not lg.is_deleted]
            snap = (
                await session.execute(select(DerivedOrm).where(DerivedOrm.baby_id == baby_id))
            ).scalar_one()
            return {
                "active_logs": len(active_logs),
                "volume_24h": snap.snapshot["feeding"]["volume_ml_24h"],
            }

    r = asyncio.run(run())
    assert r["active_logs"] == 0  # 派生行软删除。
    assert r["volume_24h"] == 0.0  # snapshot 更新（软删除事件不进窗口）。


def test_pipeline_correction_chain_updates_snapshot():
    async def run() -> dict:
        factory = get_session_factory()
        start = NOW - timedelta(hours=1)
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            old_event_id = await _seed_pending_event(
                session, family_id, baby_id, payload={"amount_ml": 100}, start=start
            )
            await session.commit()
        worker = _make_worker()
        # 先归一化旧事件 → snapshot 100。
        await worker.handle({"event_id": old_event_id, "baby_id": baby_id, "op": "insert"})
        # 纠正：correct 软删除旧事件 + 新事件 correction_of 指向旧。
        async with factory() as session:
            svc = EventService(
                repository=SqlAlchemyObservationEventRepository(session),
                clock=FixedClock(start),
                session=session,
            )
            new_event = await svc.correct(
                correction_of=old_event_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=start,
                client_created_at=start,
                normalized_payload={"amount_ml": 200},
                source=Source.MANUAL,
            )
            new_event_id = new_event.event_id
            await session.commit()
        # worker 处理新事件 → 软删除旧派生行 + 归一化新 + 重算 → snapshot 200。
        await worker.handle({"event_id": new_event_id, "baby_id": baby_id, "op": "insert"})
        async with factory() as session:
            old_logs = (
                await session.execute(select(FeedingLog).where(FeedingLog.event_id == old_event_id))
            ).scalars().all()
            old_active = [lg for lg in old_logs if not lg.is_deleted]
            snap = (
                await session.execute(select(DerivedOrm).where(DerivedOrm.baby_id == baby_id))
            ).scalar_one()
            return {
                "old_active": len(old_active),
                "volume_24h": snap.snapshot["feeding"]["volume_ml_24h"],
            }

    r = asyncio.run(run())
    assert r["old_active"] == 0  # 旧派生行软删除（纠错链）。
    assert r["volume_24h"] == 200.0  # snapshot 反映新值。
