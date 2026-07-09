# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 16:45:00

"""PostgreSQL integration tests for SQLAlchemy repository adapters.

These tests are skipped unless `PARENTING_DATABASE__URL` is set. They are intended
for Mac/Docker validation after `make infra-up` and `make db-migrate`.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from server.app.auth.domain.models import Family, Role, User
from server.app.auth.infra.sqlalchemy_repository import SQLAlchemyAuthRepository
from server.app.camera.sleep_session import SleepSessionRecord
from server.app.camera.sqlalchemy_sleep_session_repo import SQLAlchemySleepSessionRepository
from server.app.common.ids import new_ulid
from server.app.db import normalize_database_url
from server.app.events.domain.observation_event import EventSource, ObservationEventCreate
from server.app.events.infra.sqlalchemy_repository import SQLAlchemyEventRepository
from server.app.media.sqlalchemy_media_repo import SQLAlchemyMediaAssetRepository
from server.app.media.storage import MediaAssetRecord
from server.app.notification.alert_repo import AckAlertRequest, CreateAlertRequest, FeedbackRequest
from server.app.notification.channels.base import DeliveryReceipt
from server.app.notification.sqlalchemy_alert_repo import SQLAlchemyAlertRepository
from server.app.notification.sqlalchemy_delivery_repo import SQLAlchemyDeliveryRepository
from server.app.rule_engine.loader import load_rule_pack
from server.app.rule_engine.sqlalchemy_evidence_repo import SQLAlchemyEvidencePolicyRepository
from server.app.state_engine.snapshot_repo import DerivedBabyStateSnapshot
from server.app.state_engine.sqlalchemy_snapshot_repo import SQLAlchemyStateSnapshotRepository

pytestmark = pytest.mark.integration


def _db_url() -> str:
    url = os.getenv("PARENTING_DATABASE__URL") or os.getenv("PARENTING_DATABASE_URL")
    if not url:
        pytest.skip("PARENTING_DATABASE__URL not set; skipping PostgreSQL integration tests")
    return normalize_database_url(url)


@pytest.fixture(scope="session", autouse=True)
def _upgrade_database() -> None:
    url = os.getenv("PARENTING_DATABASE__URL") or os.getenv("PARENTING_DATABASE_URL")
    if not url:
        return
    env = {**os.environ, "PARENTING_DATABASE__URL": normalize_database_url(url)}
    subprocess.check_call(
        ["python3", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
    )


@pytest_asyncio.fixture()
async def engine() -> AsyncIterator[AsyncEngine]:
    db_engine = create_async_engine(_db_url(), pool_pre_ping=True)
    try:
        yield db_engine
    finally:
        await db_engine.dispose()


@pytest_asyncio.fixture()
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        transaction = await db_session.begin()
        try:
            yield db_session
        finally:
            await transaction.rollback()


async def _seed_family_user_baby(session: AsyncSession) -> tuple[Family, User, str]:
    auth_repo = SQLAlchemyAuthRepository(session)
    family = await auth_repo.add_family(Family(id=new_ulid(), name="Integration Family"))
    user = await auth_repo.add_user(
        User(id=new_ulid(), family_id=family.id, display_name="Admin", role=Role.ADMIN)
    )
    baby_id = new_ulid()
    await auth_repo.add_baby(family_id=family.id, baby_id=baby_id, name="Baby")
    return family, user, baby_id


@pytest.mark.asyncio
async def test_auth_event_state_alert_media_delivery_sleep_repositories(
    session: AsyncSession,
) -> None:
    family, user, baby_id = await _seed_family_user_baby(session)

    event_repo = SQLAlchemyEventRepository(session)
    now = datetime(2026, 7, 9, tzinfo=UTC)
    event = await event_repo.upsert(
        ObservationEventCreate(
            event_id=new_ulid(),
            baby_id=baby_id,
            family_id=family.id,
            user_id=user.id,
            event_type="feeding",
            start_time=now,
            client_created_at=now,
            source=EventSource.MANUAL,
            payload={"amount_ml": 90},
        )
    )
    repeated = await event_repo.upsert(
        ObservationEventCreate(
            event_id=event.event_id,
            baby_id=baby_id,
            family_id=family.id,
            user_id=user.id,
            event_type="feeding",
            start_time=now,
            client_created_at=now,
            source=EventSource.MANUAL,
            payload={"amount_ml": 90},
        )
    )
    assert repeated.event_id == event.event_id
    assert (await event_repo.get(event.event_id)) is not None
    assert len(await event_repo.list_by_baby(baby_id)) == 1

    state_repo = SQLAlchemyStateSnapshotRepository(session)
    snapshot = await state_repo.upsert(
        DerivedBabyStateSnapshot(
            baby_id=baby_id,
            family_id=family.id,
            snapshot={"feeding_24h_ml": 90, "source_event_count": 1},
        )
    )
    loaded_snapshot = await state_repo.get(baby_id)
    assert loaded_snapshot is not None
    assert loaded_snapshot.snapshot["feeding_24h_ml"] == snapshot.snapshot["feeding_24h_ml"]

    media_repo = SQLAlchemyMediaAssetRepository(session)
    asset = await media_repo.add(
        MediaAssetRecord(
            family_id=family.id,
            baby_id=baby_id,
            event_id=event.event_id,
            filename="photo.png",
            content_type="image/png",
            local_path="runtime/media/files/fake.bin",
        )
    )
    assert (await media_repo.get(asset.id)) is not None

    sleep_repo = SQLAlchemySleepSessionRepository(session)
    sleep = await sleep_repo.add(SleepSessionRecord(baby_id=baby_id, family_id=family.id))
    assert (await sleep_repo.get(sleep.id)).state == sleep.state

    alert_repo = SQLAlchemyAlertRepository(session)
    alert = await alert_repo.create(
        CreateAlertRequest(baby_id=baby_id, family_id=family.id, level="red", type="triage")
    )
    acked = await alert_repo.ack(alert.id, AckAlertRequest(ack_by=user.id, device_id="phone"))
    assert acked.status == "acknowledged"
    feedback = await alert_repo.feedback(
        alert.id,
        FeedbackRequest(feedback="false_positive", note="integration"),
    )
    assert feedback.feedback["type"] == "false_positive"

    delivery_repo = SQLAlchemyDeliveryRepository(session)
    receipt = await delivery_repo.add(
        DeliveryReceipt(alert_id=alert.id, channel="fcm", status="sent")
    )
    assert (await delivery_repo.list_by_alert(alert.id))[0].id == receipt.id


@pytest.mark.asyncio
async def test_evidence_policy_repository_and_audit_immutability(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            session = AsyncSession(bind=connection, expire_on_commit=False)
            repo = SQLAlchemyEvidencePolicyRepository(session)
            pack = load_rule_pack(Path("config/rules/medication/base.yaml"))
            record = await repo.activate(pack)
            current = await repo.get_current("medication", "CN")
            assert current is not None
            assert current.hash == record.hash
        finally:
            await transaction.rollback()

    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            audit_id = new_ulid()
            await connection.execute(
                text(
                    """
                    INSERT INTO audit_log (id, actor, action, resource)
                    VALUES (:id, CAST(:actor AS jsonb), :action, :resource)
                    """
                ),
                {
                    "id": audit_id,
                    "actor": json.dumps({"actor_kind": "integration"}),
                    "action": "integration.insert",
                    "resource": "audit_log",
                },
            )
            with pytest.raises(SQLAlchemyError):
                await connection.execute(
                    text("UPDATE audit_log SET action='mutated' WHERE id=:id"),
                    {"id": audit_id},
                )
        finally:
            await transaction.rollback()
