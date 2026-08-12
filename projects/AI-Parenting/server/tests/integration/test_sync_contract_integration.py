# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-12 00:00:00
"""同步契约校验 → EventService 集成测试（APC-T012，需 DB）。

验证验收标准"非法同步事件不会进入业务处理"的端到端链路：
    - 合法同步记录经 ``validate_sync_contract`` → ObservationEvent → EventService.record 写入 PG。
    - 非法同步记录（缺字段/ULID 错/source 非法）被 validator 拦截（ValidationError），
      不进入 EventService，DB 无新行。
    - validator 产出的 event 写入后 sync_status=synced、processing_status=pending（独立状态机）。

连 AI_parenting_dev 库；单 asyncio.run（与 test_event_repository 一致，避免跨循环死连接）。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select

from server.app import db as db_module
from server.app.common.clock import SystemClock
from server.app.common.errors import ValidationError
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family
from server.app.models.events import ObservationEvent as Orm
from server.app.sync.service.contract_validator import validate_sync_contract

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 11, 8, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_db():
    """同步重置进程级 engine 缓存（避免跨测试死连接，与 test_event_repository 一致）。"""
    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_and_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="同步契约测试家", timezone="Asia/Shanghai")
    session.add(family)
    await session.flush()
    baby = Baby(id=new_id(), family_id=family.id, birth_date=date(2026, 6, 1), sex="male")
    session.add(baby)
    await session.flush()
    return family.id, baby.id


def _make_service(session) -> EventService:
    return EventService(
        repository=SqlAlchemyObservationEventRepository(session),
        clock=SystemClock(),
        session=session,
    )


def test_valid_sync_record_persists_via_event_service():
    """合法同步记录：validator → EventService.record → 写入 PG，双状态字段正确。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            event_id = new_id()
            record = {
                "event_id": event_id,
                "baby_id": baby_id,
                "family_id": family_id,
                "event_type": "feeding",
                "client_created_at": NOW.isoformat(),
                "payload": {"amount_ml": 120},
                "source": "manual",
            }
            # validator 校验 + 构造 ObservationEvent（sync_status=synced, processing=pending）。
            ev = validate_sync_contract(record)
            assert ev.sync_status.value == "synced"
            assert ev.processing_status.value == "pending"
            # EventService.record 写入 PG（server_received_at 由 service 用 Clock 覆盖）。
            # 传入 validator 产出的双状态字段（synced/pending），否则 record 用默认 pending。
            svc = _make_service(session)
            written = await svc.record(
                event_id=ev.event_id,
                baby_id=ev.baby_id,
                family_id=ev.family_id,
                event_type=ev.event_type,
                start_time=ev.start_time,
                client_created_at=ev.client_created_at,
                normalized_payload=ev.normalized_payload,
                source=ev.source,
                sync_status=ev.sync_status,
                processing_status=ev.processing_status,
            )
            await session.commit()
            # DB 读回验证。
            stmt = select(Orm).where(Orm.id == event_id)
            orm = (await session.execute(stmt)).scalar_one()
            return {
                "event_id": orm.id,
                "sync_status": orm.sync_status,
                "processing_status": orm.processing_status,
                "amount_ml": orm.normalized_payload.get("amount_ml"),
                "written_event_id": written.event_id,
            }

    r = asyncio.run(run())
    assert r["event_id"] == r["written_event_id"]
    assert r["sync_status"] == "synced"
    assert r["processing_status"] == "pending"
    assert r["amount_ml"] == 120


def test_invalid_sync_record_blocked_before_event_service():
    """非法同步记录（缺 payload）被 validator 拦截，不进入 EventService，DB 无新行。"""

    async def run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            record = {
                "event_id": new_id(),
                "baby_id": baby_id,
                "family_id": family_id,
                "event_type": "feeding",
                "client_created_at": NOW.isoformat(),
                # 缺 payload 与 source。
                "source": "manual",
            }
            # validator 抛 ValidationError，不进入 EventService。
            with pytest.raises(ValidationError):
                ev = validate_sync_contract(record)
                svc = _make_service(session)
                await svc.record(
                    event_id=ev.event_id,
                    baby_id=ev.baby_id,
                    family_id=ev.family_id,
                    event_type=ev.event_type,
                    start_time=ev.start_time,
                    client_created_at=ev.client_created_at,
                    normalized_payload=ev.normalized_payload,
                    source=ev.source,
                )
            await session.commit()
            # DB 无新 observation_event 行（除前置无写入）。
            stmt = select(Orm).where(Orm.family_id == family_id)
            rows = (await session.execute(stmt)).scalars().all()
            return len(rows)

    count = asyncio.run(run())
    assert count == 0, "非法记录不应进入 EventService，DB 不应有新行"


def test_invalid_ulid_blocked_before_event_service():
    """ULID 非法被 validator 拦截，不进入 EventService。"""

    async def run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_and_baby(session)
            record = {
                "event_id": "not-a-ulid",
                "baby_id": baby_id,
                "family_id": family_id,
                "event_type": "feeding",
                "client_created_at": NOW.isoformat(),
                "payload": {"amount_ml": 120},
                "source": "manual",
            }
            with pytest.raises(ValidationError):
                ev = validate_sync_contract(record)
                svc = _make_service(session)
                await svc.record(
                    event_id=ev.event_id,
                    baby_id=ev.baby_id,
                    family_id=ev.family_id,
                    event_type=ev.event_type,
                    start_time=ev.start_time,
                    client_created_at=ev.client_created_at,
                    normalized_payload=ev.normalized_payload,
                    source=ev.source,
                )
            await session.commit()
            stmt = select(Orm).where(Orm.family_id == family_id)
            return len((await session.execute(stmt)).scalars().all())

    assert asyncio.run(run()) == 0
