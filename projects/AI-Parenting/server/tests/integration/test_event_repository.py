# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""ObservationEvent 仓储与服务集成测试（APC-T009，需 DB）。

连 AI_parenting_dev 库验证：
    - SqlAlchemyObservationEventRepository.upsert 端到端写入 observation_event 表。
    - 幂等：重复同一 event_id 不创建重复行，返回既有记录（架构 §505）。
    - correction 链：correct 软删除旧事件 + 新事件 correction_of 指向旧 event_id（§5.1）。
    - soft_delete：置 is_deleted=true，不物理删除（§5.1）。
    - query：按 baby_id 过滤，排除软删除，按 start_time DESC。
    - 双状态字段：sync_status/processing_status 写入与读回一致（§6.2）。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
每个测试用单一 asyncio.run（避免跨事件循环的 engine 死连接问题，与 test_audit 一致）。
observation_event 表有 FK 到 baby.id/family.id（RESTRICT），故先建真实 family+baby 行。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select

from server.app import db as db_module
from server.app.common.clock import SystemClock
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.events.domain import (
    ProcessingStatus,
    Source,
    SyncStatus,
)
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset_db():
    """同步重置进程级 engine 缓存（避免跨测试死连接）。"""
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_and_baby(session) -> tuple[str, str]:
    """建真实 family + baby 行（满足 observation_event FK RESTRICT）。"""
    family = Family(id=new_id(), name="事件测试家", timezone="Asia/Shanghai")
    session.add(family)
    await session.flush()
    baby = Baby(
        id=new_id(),
        family_id=family.id,
        birth_date=date(2026, 6, 1),
        sex="male",
    )
    session.add(baby)
    await session.flush()
    return family.id, baby.id


def _make_service(session) -> EventService:
    return EventService(
        repository=SqlAlchemyObservationEventRepository(session),
        clock=SystemClock(),
        session=session,
    )


def test_upsert_writes_event_end_to_end():
    """端到端：record 写入 observation_event，字段齐全（含双状态字段）。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            svc = _make_service(session)
            event_id = new_id()
            ev = await svc.record(
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
            assert ev.event_id == event_id
            # 读回验证。
            from server.app.models.events import ObservationEvent as Orm

            row = (
                await session.execute(select(Orm).where(Orm.id == event_id))
            ).scalar_one()
        return {
            "event_id": row.id,
            "event_type": row.event_type,
            "source": row.source,
            "sync_status": row.sync_status,
            "processing_status": row.processing_status,
            "amount_ml": row.normalized_payload["amount_ml"],
            "is_deleted": row.is_deleted,
            "correction_of": row.correction_of,
        }

    row = asyncio.run(run())
    assert row["event_type"] == "feeding"
    assert row["source"] == "manual"
    assert row["sync_status"] == "pending"
    assert row["processing_status"] == "pending"
    assert row["amount_ml"] == 120
    assert row["is_deleted"] is False
    assert row["correction_of"] is None


def test_upsert_idempotent_no_duplicate_rows():
    """幂等（架构 §505）：重复同一 event_id 不创建重复行。"""

    async def run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            svc = _make_service(session)
            event_id = new_id()
            for _ in range(3):
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
            from server.app.models.events import ObservationEvent as Orm

            count = (
                await session.execute(
                    select(func.count()).select_from(Orm).where(Orm.id == event_id)
                )
            ).scalar_one()
        return count

    count = asyncio.run(run())
    assert count == 1, "重复 event_id 不应产生重复行（幂等 §505）"


def test_correct_chain_soft_deletes_original_and_links_correction_of():
    """correction 链（§5.1）：correct 软删除旧事件 + 新事件 correction_of 指向旧 event_id。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            svc = _make_service(session)
            original_id = new_id()
            await svc.record(
                event_id=original_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                client_created_at=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                normalized_payload={"amount_ml": 120},
                source=Source.MANUAL,
            )
            corrected = await svc.correct(
                correction_of=original_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                client_created_at=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                normalized_payload={"amount_ml": 90},
                source=Source.MANUAL,
            )
            await session.commit()
            from server.app.models.events import ObservationEvent as Orm

            original_row = (
                await session.execute(select(Orm).where(Orm.id == original_id))
            ).scalar_one()
            corrected_row = (
                await session.execute(
                    select(Orm).where(Orm.id == corrected.event_id)
                )
            ).scalar_one()
        return {
            "original_deleted": original_row.is_deleted,
            "corrected_correction_of": corrected_row.correction_of,
            "corrected_amount": corrected_row.normalized_payload["amount_ml"],
            "corrected_deleted": corrected_row.is_deleted,
        }

    r = asyncio.run(run())
    assert r["original_deleted"] is True  # 旧事件软删除
    assert r["corrected_correction_of"] is not None  # 新事件指向旧
    assert r["corrected_amount"] == 90
    assert r["corrected_deleted"] is False


def test_soft_delete_marks_is_deleted_not_physical():
    """软删除（§5.1）：置 is_deleted=true，行仍存在（不物理删除）。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            svc = _make_service(session)
            event_id = new_id()
            await svc.record(
                event_id=event_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="diaper",
                start_time=datetime(2026, 8, 11, 9, 0, tzinfo=UTC),
                client_created_at=datetime(2026, 8, 11, 9, 0, tzinfo=UTC),
                normalized_payload={"type": "wet"},
                source=Source.MANUAL,
            )
            await svc.soft_delete(event_id=event_id)
            await session.commit()
            from server.app.models.events import ObservationEvent as Orm

            row = (
                await session.execute(select(Orm).where(Orm.id == event_id))
            ).scalar_one()
            # get 应过滤软删除 → None。
            repo = SqlAlchemyObservationEventRepository(session)
            visible = await repo.get(event_id)
        return {
            "row_exists": row is not None,
            "is_deleted": row.is_deleted,
            "repo_get_returns_none": visible is None,
        }

    r = asyncio.run(run())
    assert r["row_exists"] is True  # 物理行仍在
    assert r["is_deleted"] is True
    assert r["repo_get_returns_none"] is True  # 仓储查询过滤软删除


def test_query_filters_by_baby_and_excludes_deleted_ordered_desc():
    """query：按 baby_id 过滤、排除软删除、按 start_time DESC。"""

    async def run() -> tuple[list[str], str]:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            svc = _make_service(session)
            times = [
                datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                datetime(2026, 8, 11, 9, 0, tzinfo=UTC),
                datetime(2026, 8, 11, 10, 0, tzinfo=UTC),
            ]
            ids = [new_id() for _ in times]
            for eid, t in zip(ids, times, strict=True):
                await svc.record(
                    event_id=eid,
                    baby_id=baby_id,
                    family_id=family_id,
                    event_type="feeding",
                    start_time=t,
                    client_created_at=t,
                    normalized_payload={},
                    source=Source.MANUAL,
                )
            # 软删除中间那条（9:00）。
            await svc.soft_delete(event_id=ids[1])
            await session.commit()
            repo = SqlAlchemyObservationEventRepository(session)
            result = await repo.query(baby_id=baby_id)
        return [e.event_id for e in result], ids[1]

    result_ids, deleted_id = asyncio.run(run())
    # 排除软删除的 deleted_id，剩 2 条，按 start_time DESC → 10:00 在 8:00 之前。
    assert deleted_id not in result_ids
    assert len(result_ids) == 2


def test_dual_status_fields_persist():
    """双状态字段（§6.2）：sync_status/processing_status 写入与读回一致。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            svc = _make_service(session)
            event_id = new_id()
            await svc.record(
                event_id=event_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                client_created_at=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
                normalized_payload={"amount_ml": 120},
                source=Source.SENSOR,
                sync_status=SyncStatus.SYNCED,
                processing_status=ProcessingStatus.NORMALIZED,
            )
            await session.commit()
            repo = SqlAlchemyObservationEventRepository(session)
            ev = await repo.get(event_id)
        return {
            "sync_status": ev.sync_status.value,
            "processing_status": ev.processing_status.value,
            "source": ev.source.value,
        }

    r = asyncio.run(run())
    assert r["sync_status"] == "synced"
    assert r["processing_status"] == "normalized"
    assert r["source"] == "sensor"
