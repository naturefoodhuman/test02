# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""Normalization 集成测试（APC-T013，需 DB）。

验证端到端：
    - manual feeding 事件经 NormalizationService → 写 feeding_log（结构化列）+ 推进 processing_status=normalized。
    - voice_text feeding 事件 → 写 feeding_log（amount_ml 从文本解析）。
    - 幂等：重复 normalize 同一 event_id 不重复写 feeding_log。
    - 不识别 event_type（milestone）→ 不写派生表、processing_status 不推进。
    - diaper 事件 → 写 diaper_log（payload jsonb）。

连 AI_parenting_dev 库；单 asyncio.run + _reset_db autouse（与 test_event_repository 一致）。
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
from server.app.events.domain import (
    Source,
    SyncStatus,
)
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family
from server.app.models.events import ObservationEvent as Orm
from server.app.models.logs import DiaperLog, FeedingLog
from server.app.normalization.infra.log_writer import SqlAlchemyLogWriter
from server.app.normalization.service import NormalizationService

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 13, 8, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_db():
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_and_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="归一化测试家", timezone="Asia/Shanghai")
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
    raw_input=None,
) -> str:
    """经 EventService.record 写入 observation_event（满足 FK + 真实链路）。

    payload=None 时用 feeding 默认载荷；传 payload={}（空 dict）则按空载荷写入
    （voice 测试需要空 normalized_payload 以验证从文本解析）。
    """
    event_id = new_id()
    svc = EventService(
        repository=SqlAlchemyObservationEventRepository(session),
        clock=SystemClock(),
        session=session,
    )
    if payload is None:
        payload = {"amount_ml": 120, "feeding_type": "bottle"}
    await svc.record(
        event_id=event_id,
        baby_id=baby_id,
        family_id=family_id,
        event_type=event_type,
        start_time=NOW,
        client_created_at=NOW,
        normalized_payload=payload,
        source=source,
        raw_input=raw_input,
        sync_status=SyncStatus.SYNCED,
    )
    return event_id


def test_manual_feeding_normalizes_to_feeding_log():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_event(session, family_id, baby_id)
            # 取回事件实体（NormalizationService 消费 domain.ObservationEvent）。
            repo = SqlAlchemyObservationEventRepository(session)
            ev = await repo.get(event_id)
            assert ev is not None
            # 归一化。
            norm_svc = NormalizationService(
                repository=repo, log_writer=SqlAlchemyLogWriter(session)
            )
            record = await norm_svc.normalize(ev)
            await session.commit()
            assert record is not None
            # 读回 feeding_log。
            fl = (
                await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id))
            ).scalar_one()
            # processing_status 推进。
            orm = (await session.execute(select(Orm).where(Orm.id == event_id))).scalar_one()
            # 只查本 event_id 的 log（避免其他测试残留干扰）。
            log_count = len(
                (await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id)))
                .scalars()
                .all()
            )
            return {
                "amount_ml": fl.amount_ml,
                "feeding_type": fl.feeding_type,
                "processing_status": orm.processing_status,
                "log_count": log_count,
            }

    r = asyncio.run(run())
    assert r["amount_ml"] == 120
    assert r["feeding_type"] == "bottle"
    assert r["processing_status"] == "normalized"
    assert r["log_count"] == 1


def test_voice_feeding_parses_amount_from_text():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_event(
                session,
                family_id,
                baby_id,
                source=Source.VOICE_TEXT,
                payload={},
                raw_input={"text": "刚喂了90ml奶"},
            )
            repo = SqlAlchemyObservationEventRepository(session)
            ev = await repo.get(event_id)
            assert ev is not None
            norm_svc = NormalizationService(
                repository=repo, log_writer=SqlAlchemyLogWriter(session)
            )
            record = await norm_svc.normalize(ev)
            await session.commit()
            assert record is not None
            fl = (
                await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id))
            ).scalar_one()
            return {"amount_ml": fl.amount_ml, "confidence": record.confidence}

    r = asyncio.run(run())
    assert r["amount_ml"] == 90
    assert r["confidence"] < 1.0


def test_idempotent_no_duplicate_log():
    async def run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_event(session, family_id, baby_id)
            repo = SqlAlchemyObservationEventRepository(session)
            ev = await repo.get(event_id)
            norm_svc = NormalizationService(
                repository=repo, log_writer=SqlAlchemyLogWriter(session)
            )
            await norm_svc.normalize(ev)
            # 第二次归一化（幂等）。
            ev2 = await repo.get(event_id)
            await norm_svc.normalize(ev2)
            await session.commit()
            return len(
                (await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id)))
                .scalars()
                .all()
            )

    assert asyncio.run(run()) == 1


def test_non_p0_event_type_no_log_no_advance():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_event(
                session, family_id, baby_id, event_type="milestone", payload={}
            )
            repo = SqlAlchemyObservationEventRepository(session)
            ev = await repo.get(event_id)
            norm_svc = NormalizationService(
                repository=repo, log_writer=SqlAlchemyLogWriter(session)
            )
            record = await norm_svc.normalize(ev)
            await session.commit()
            orm = (await session.execute(select(Orm).where(Orm.id == event_id))).scalar_one()
            # 只查本 event_id 的 log（应为 0，避免其他测试残留干扰）。
            log_count = len(
                (await session.execute(select(FeedingLog).where(FeedingLog.event_id == event_id)))
                .scalars()
                .all()
            )
            return {
                "record": record,
                "processing_status": orm.processing_status,
                "log_count": log_count,
            }

    r = asyncio.run(run())
    assert r["record"] is None
    assert r["processing_status"] == "pending"  # 未推进。
    assert r["log_count"] == 0


def test_diaper_normalizes_to_diaper_log():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = await _seed_event(
                session,
                family_id,
                baby_id,
                event_type="diaper",
                payload={"type": "wet"},
            )
            repo = SqlAlchemyObservationEventRepository(session)
            ev = await repo.get(event_id)
            norm_svc = NormalizationService(
                repository=repo, log_writer=SqlAlchemyLogWriter(session)
            )
            record = await norm_svc.normalize(ev)
            await session.commit()
            dl = (
                await session.execute(select(DiaperLog).where(DiaperLog.event_id == event_id))
            ).scalar_one()
            return {
                "table": record.table if record else None,
                "payload_type": dl.payload.get("type"),
            }

    r = asyncio.run(run())
    assert r["table"] == "diaper_log"
    assert r["payload_type"] == "wet"
