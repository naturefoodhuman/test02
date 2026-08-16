# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""State Engine 集成测试（APC-T016，需 DB）。

两部分：
    1. DB 重算（asyncio.run + reset_db）：事件 → StateEngine.recompute → snapshot upsert +
       processing_status 推进 projected；幂等重算。
    2. API（TestClient + dependency_overrides）：GET /babies/{id}/state 鉴权（state:read）+
       baby 归属校验 + 返回最新快照。

连 AI_parenting_dev 库。
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from server.app import db as db_module
from server.app.auth.domain import Principal, Role
from server.app.common.clock import FixedClock
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.events.domain import ProcessingStatus, Source, SyncStatus
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.idempotency import EventService
from server.app.main import clear_workers, create_app
from server.app.models.core import Baby, Family
from server.app.models.derived import DerivedBabyState as DerivedOrm
from server.app.models.events import ObservationEvent as Orm
from server.app.settings import get_settings
from server.app.state_engine.engine import StateEngine
from server.app.state_engine.infra import SqlAlchemyEventLoader
from server.app.state_engine.snapshot_repo import SqlAlchemySnapshotRepository

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 16, 8, 0, 0, tzinfo=UTC)


# ---- DB 重算测试 ----


@pytest.fixture(autouse=True)
def _reset_db():
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_and_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="state 测试家", timezone="Asia/Shanghai")
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
    payload=None,
    processing_status=ProcessingStatus.NORMALIZED,
    start=None,
) -> str:
    event_id = new_id()
    if start is None:
        start = NOW - timedelta(hours=1)
    svc = EventService(
        repository=SqlAlchemyObservationEventRepository(session),
        clock=FixedClock(start),
        session=session,
    )
    if payload is None:
        payload = {"amount_ml": 120, "feeding_type": "bottle"}
    await svc.record(
        event_id=event_id,
        baby_id=baby_id,
        family_id=family_id,
        event_type=event_type,
        start_time=start,
        client_created_at=start,
        normalized_payload=payload,
        source=Source.MANUAL,
        sync_status=SyncStatus.SYNCED,
        processing_status=processing_status,
    )
    return event_id


def test_recompute_upserts_snapshot_and_advances_projected():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            eid = await _seed_event(session, family_id, baby_id)
            await session.commit()
        # 独立 session 重算。
        async with factory() as session:
            engine = StateEngine(
                event_loader=SqlAlchemyEventLoader(session),
                snapshot_repo=SqlAlchemySnapshotRepository(session),
                event_repo=SqlAlchemyObservationEventRepository(session),
                clock=FixedClock(NOW),
            )
            await engine.recompute(baby_id)
            await session.commit()
        # 读回验证。
        async with factory() as session:
            snap = (
                await session.execute(select(DerivedOrm).where(DerivedOrm.baby_id == baby_id))
            ).scalar_one()
            ev = (await session.execute(select(Orm).where(Orm.id == eid))).scalar_one()
            return {
                "volume_ml": snap.snapshot["feeding"]["volume_ml_24h"],
                "computed_at": snap.computed_at,
                "processing_status": ev.processing_status,
            }

    r = asyncio.run(run())
    assert r["volume_ml"] == 120.0
    assert r["computed_at"] == NOW
    assert r["processing_status"] == "projected"


def test_recompute_idempotent_overwrites_snapshot():
    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            await _seed_event(session, family_id, baby_id)
            await session.commit()
        async with factory() as session:
            engine = StateEngine(
                event_loader=SqlAlchemyEventLoader(session),
                snapshot_repo=SqlAlchemySnapshotRepository(session),
                event_repo=SqlAlchemyObservationEventRepository(session),
                clock=FixedClock(NOW),
            )
            await engine.recompute(baby_id)
            await session.commit()
        async with factory() as session:
            engine = StateEngine(
                event_loader=SqlAlchemyEventLoader(session),
                snapshot_repo=SqlAlchemySnapshotRepository(session),
                event_repo=SqlAlchemyObservationEventRepository(session),
                clock=FixedClock(NOW),
            )
            await engine.recompute(baby_id)
            await session.commit()
        async with factory() as session:
            rows = (
                (await session.execute(select(DerivedOrm).where(DerivedOrm.baby_id == baby_id)))
                .scalars()
                .all()
            )
            return {"rows": len(rows)}

    assert asyncio.run(run())["rows"] == 1  # 单行 per baby（upsert 覆盖）。


# ---- API 测试 ----


@pytest.fixture
def client_with_principal() -> Iterator[tuple[TestClient, str]]:
    """TestClient + 注入固定 Principal（family_id 由测试 seed 后填入）。"""
    get_settings.cache_clear()
    db_module.reset_db()
    clear_workers()
    settings = get_settings()
    app = create_app(settings)

    captured: dict[str, str] = {}

    from server.app.di import get_principal_dep

    def _override_principal():
        return Principal(
            user_id=new_id(),
            family_id=captured["family_id"],
            role=Role.ADMIN,
        )

    app.dependency_overrides[get_principal_dep] = _override_principal
    with TestClient(app) as c:
        yield c, captured
    db_module.reset_db()


def test_state_api_returns_snapshot_after_recompute(client_with_principal):
    client, captured = client_with_principal

    async def seed() -> str:
        factory = get_session_factory()
        async with factory() as session:
            family = Family(id=new_id(), name="api 家", timezone="Asia/Shanghai")
            session.add(family)
            await session.flush()
            baby = Baby(id=new_id(), family_id=family.id, birth_date=date(2026, 6, 1), sex="male")
            session.add(baby)
            await session.flush()
            captured["family_id"] = family.id
            await _seed_event(
                session, family.id, baby.id, start=datetime.now(UTC) - timedelta(hours=1)
            )
            await session.commit()
        # 释放 seed loop 的 engine，TestClient 请求时重建绑定其 loop（避免跨 loop）。
        await db_module.dispose_db()
        db_module.reset_db()
        return baby.id

    baby_id = asyncio.run(seed())

    # 首次查询无快照 → 懒重算 → 返回。
    resp = client.get(f"/api/v1/babies/{baby_id}/state")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["baby_id"] == baby_id
    assert body["feeding"]["volume_ml_24h"] == 120.0
    assert body["computed_at"] is not None


def test_state_api_404_for_baby_not_in_family(client_with_principal):
    client, captured = client_with_principal

    async def seed() -> tuple[str, str]:
        factory = get_session_factory()
        async with factory() as session:
            fam = Family(id=new_id(), name="fam1", timezone="Asia/Shanghai")
            session.add(fam)
            await session.flush()
            baby = Baby(id=new_id(), family_id=fam.id, birth_date=date(2026, 6, 1), sex="male")
            session.add(baby)
            await session.flush()
            captured["family_id"] = fam.id  # principal 属于 fam1。
            other_fam = Family(id=new_id(), name="fam2", timezone="Asia/Shanghai")
            session.add(other_fam)
            await session.flush()
            other_baby = Baby(
                id=new_id(), family_id=other_fam.id, birth_date=date(2026, 6, 1), sex="male"
            )
            session.add(other_baby)
            await session.flush()
            await session.commit()
        await db_module.dispose_db()
        db_module.reset_db()
        return baby.id, other_baby.id

    _own_baby, other_baby = asyncio.run(seed())

    # 查询别家 baby → 404（不泄露存在性）。
    resp = client.get(f"/api/v1/babies/{other_baby}/state")
    assert resp.status_code == 404, resp.text


def test_state_api_401_without_token():
    """无 dependency_override 时，缺 Bearer token → 401。"""
    get_settings.cache_clear()
    db_module.reset_db()
    clear_workers()
    settings = get_settings()
    app = create_app(settings)
    with TestClient(app) as c:
        resp = c.get(f"/api/v1/babies/{new_id()}/state")
    assert resp.status_code == 401, resp.text
    db_module.reset_db()
