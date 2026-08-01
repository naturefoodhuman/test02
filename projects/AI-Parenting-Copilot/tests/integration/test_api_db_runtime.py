# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 23:20:00

"""DB-backed FastAPI runtime smoke tests.

Skipped unless PARENTING_DATABASE__URL is set. These tests validate that API routes
switch from in-memory repositories to SQLAlchemy repositories when a DB URL is configured.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from server.app.auth.infra.sqlalchemy_repository import SQLAlchemyAuthRepository
from server.app.common.ids import new_ulid
from server.app.db import normalize_database_url
from server.app.main import create_app
from server.app.memory.sqlalchemy_store import SQLAlchemyMemoryStore
from server.app.normalization.worker import PendingEventProcessor
from server.app.state_engine.snapshot_repo import DerivedBabyStateSnapshot
from server.app.state_engine.sqlalchemy_snapshot_repo import SQLAlchemyStateSnapshotRepository

pytestmark = pytest.mark.integration


def _db_url() -> str:
    url = os.getenv("PARENTING_DATABASE__URL") or os.getenv("PARENTING_DATABASE_URL")
    if not url:
        pytest.skip("PARENTING_DATABASE__URL not set; skipping DB-backed API smoke tests")
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


@pytest.mark.asyncio
async def test_db_backed_auth_event_alert_state_and_rules_api(
    engine: AsyncEngine,
    tmp_path: Path,
) -> None:
    family_id: str | None = None
    baby_id: str | None = None
    alert_id: str | None = None
    integration_rule_version = new_ulid()

    try:
        app = create_app()
        with TestClient(app) as client:
            init = client.post(
                "/api/v1/auth/init-family",
                json={
                    "family_name": f"DB API Family {new_ulid()}",
                    "admin_display_name": "DB Admin",
                    "admin_secret": "secret123",
                },
            )
            assert init.status_code == 200
            init_payload = init.json()
            token = init_payload["access_token"]
            family_id = init_payload["family_id"]
            admin_user_id = init_payload["admin_user_id"]

            # The Auth API creates family/admin; seed a baby into that same family through
            # the DB adapter so Events/State APIs can validate real foreign keys.
            async with async_sessionmaker(engine, expire_on_commit=False)() as seed_session:
                async with seed_session.begin():
                    await SQLAlchemyAuthRepository(seed_session).add_baby(
                        family_id=family_id,
                        baby_id=(baby_id := new_ulid()),
                        name="DB Baby",
                    )
                    await seed_session.execute(
                        text(
                            """
                            INSERT INTO family_knowledge (id, family_id, key, value)
                            VALUES (:id, :family_id, :key, CAST(:value AS jsonb))
                            """
                        ),
                        {
                            "id": new_ulid(),
                            "family_id": family_id,
                            "key": "sleep.preference",
                            "value": '{"value":"white_noise"}',
                        },
                    )

            device = client.post(
                "/api/v1/auth/devices/register",
                headers={"authorization": f"Bearer {token}"},
                json={"kind": "phone", "name": "DB phone"},
            )
            assert device.status_code == 200
            device_id = device.json()["device_id"]

            now = datetime.now(UTC).replace(microsecond=0).isoformat()
            event = client.post(
                "/api/v1/events",
                json={
                    "event_id": new_ulid(),
                    "baby_id": baby_id,
                    "family_id": family_id,
                    "user_id": admin_user_id,
                    "device_id": device_id,
                    "event_type": "feeding",
                    "start_time": now,
                    "client_created_at": now,
                    "source": "manual",
                    "payload": {"amount_ml": 90},
                },
            )
            assert event.status_code == 200
            listed = client.get("/api/v1/events", params={"baby_id": baby_id})
            assert listed.status_code == 200
            assert listed.json()[0]["event_type"] == "feeding"

            async with async_sessionmaker(engine, expire_on_commit=False)() as worker_session:
                async with worker_session.begin():
                    await PendingEventProcessor(worker_session).process_pending()
            state_from_pipeline = client.get(f"/api/v1/babies/{baby_id}/state")
            assert state_from_pipeline.status_code == 200
            assert state_from_pipeline.json()["snapshot"]["feeding_24h_ml"] == 90

            async with async_sessionmaker(engine, expire_on_commit=False)() as memory_session:
                memory = await SQLAlchemyMemoryStore(memory_session).build_snapshot(
                    baby_id=baby_id,
                    family_id=family_id,
                )
            assert memory.hard_facts["name"] == "DB Baby"
            assert memory.family_preferences["sleep.preference"] == {"value": "white_noise"}
            assert memory.behavior_baseline["feeding_24h_ml"] == 90
            assert memory.short_context["event_type_counts"] == {"feeding": 1}

            alert = client.post(
                "/api/v1/alerts",
                json={"baby_id": baby_id, "family_id": family_id, "level": "red", "type": "triage"},
            )
            assert alert.status_code == 200
            alert_id = alert.json()["id"]
            ack = client.post(
                f"/api/v1/alerts/{alert_id}/ack",
                json={"ack_by": admin_user_id},
            )
            assert ack.status_code == 200
            assert ack.json()["status"] == "acknowledged"

            rule_pack = tmp_path / "rule.yaml"
            rule_pack.write_text(
                "\n".join(
                    [
                        "policy_type: integration",
                        "domain: integration",
                        "region: CN",
                        f"version: {integration_rule_version}",
                        "effective_from: '2026-07-09'",
                        "source: integration-test",
                        "rules: []",
                    ]
                )
            )
            activated = client.post(
                "/api/v1/rules/activate",
                headers={"x-role": "Admin"},
                json={"path": str(rule_pack)},
            )
            assert activated.status_code == 200
            assert activated.json()["activated"]["policy_type"] == "integration"

        async with engine.connect() as audit_connection:
            audit_actions = set(
                await audit_connection.scalars(
                    text(
                        """
                        SELECT action FROM audit_log
                        WHERE resource IN (
                            :family_resource,
                            :event_resource,
                            :alert_resource,
                            :rule_resource
                        )
                        """
                    ),
                    {
                        "family_resource": f"family:{family_id}",
                        "event_resource": f"observation_event:{event.json()['event_id']}",
                        "alert_resource": f"alert:{alert_id}",
                        "rule_resource": f"evidence_policy:integration:{integration_rule_version}",
                    },
                )
            )
            assert {"auth.init_family", "event.upsert", "alert.create", "rule.activate"}.issubset(
                audit_actions
            )

        async with async_sessionmaker(engine, expire_on_commit=False)() as state_session:
            async with state_session.begin():
                await SQLAlchemyStateSnapshotRepository(state_session).upsert(
                    DerivedBabyStateSnapshot(
                        baby_id=baby_id,
                        family_id=family_id,
                        snapshot={"feeding_24h_ml": 90},
                    )
                )
        app = create_app()
        with TestClient(app) as client:
            state = client.get(f"/api/v1/babies/{baby_id}/state")
            assert state.status_code == 200
            assert state.json()["snapshot"]["feeding_24h_ml"] == 90
    finally:
        if family_id is not None:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        """
                        DELETE FROM alert_delivery
                        WHERE alert_id IN (SELECT id FROM alert WHERE family_id = :family_id)
                        """
                    ),
                    {"family_id": family_id},
                )
                for statement in [
                    "DELETE FROM alert WHERE family_id = :family_id",
                    "DELETE FROM media_asset WHERE family_id = :family_id",
                    "DELETE FROM camera_event WHERE session_id IN "
                    "(SELECT id FROM sleep_session WHERE family_id = :family_id)",
                    "DELETE FROM sleep_session WHERE family_id = :family_id",
                    "DELETE FROM derived_baby_state WHERE family_id = :family_id",
                    "DELETE FROM feeding_log WHERE family_id = :family_id",
                    "DELETE FROM diaper_log WHERE family_id = :family_id",
                    "DELETE FROM sleep_log WHERE family_id = :family_id",
                    "DELETE FROM temperature_log WHERE family_id = :family_id",
                    "DELETE FROM supplement_log WHERE family_id = :family_id",
                    "DELETE FROM vaccine_record WHERE family_id = :family_id",
                    "DELETE FROM medication_log WHERE family_id = :family_id",
                    "DELETE FROM symptom_event WHERE family_id = :family_id",
                    "DELETE FROM growth_log WHERE family_id = :family_id",
                    "DELETE FROM milestone_log WHERE family_id = :family_id",
                    "DELETE FROM jaundice_photo WHERE family_id = :family_id",
                    "DELETE FROM solid_food_log WHERE family_id = :family_id",
                    "DELETE FROM mother_health WHERE family_id = :family_id",
                    "DELETE FROM observation_event WHERE family_id = :family_id",
                    "DELETE FROM sensor_event WHERE device_id IN "
                    "(SELECT id FROM device WHERE family_id = :family_id)",
                    "DELETE FROM device WHERE family_id = :family_id",
                    'DELETE FROM "user" WHERE family_id = :family_id',
                    "DELETE FROM baby WHERE family_id = :family_id",
                    "DELETE FROM family_knowledge WHERE family_id = :family_id",
                    "DELETE FROM sync_state WHERE family_id = :family_id",
                    "DELETE FROM family WHERE id = :family_id",
                ]:
                    await connection.execute(text(statement), {"family_id": family_id})
                await connection.execute(
                    text("DELETE FROM evidence_policy WHERE policy_type = 'integration'"),
                )
