# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 19:30:00

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
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from server.app.auth.domain.models import Family
from server.app.auth.infra.sqlalchemy_repository import SQLAlchemyAuthRepository
from server.app.common.ids import new_ulid
from server.app.db import normalize_database_url
from server.app.main import create_app
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
    session: AsyncSession,
    tmp_path: Path,
) -> None:
    family_id = new_ulid()
    baby_id = new_ulid()
    family_name = f"DB API Family {family_id}"
    admin_secret = "secret123"
    # Seed baby via repository before exercising API-created user/device/event/state.
    auth_repo = SQLAlchemyAuthRepository(session)
    await auth_repo.add_family(Family(id=family_id, name=family_name))
    await auth_repo.add_baby(family_id=family_id, baby_id=baby_id, name="DB Baby")
    await session.commit()

    app = create_app()
    with TestClient(app) as client:
        init = client.post(
            "/api/v1/auth/init-family",
            json={
                "family_name": f"{family_name} API",
                "admin_display_name": "DB Admin",
                "admin_secret": admin_secret,
            },
        )
        assert init.status_code == 200
        init_payload = init.json()
        token = init_payload["access_token"]

        device = client.post(
            "/api/v1/auth/devices/register",
            headers={"authorization": f"Bearer {token}"},
            json={"kind": "phone", "name": "DB phone"},
        )
        assert device.status_code == 200
        device_id = device.json()["device_id"]

        now = datetime(2026, 7, 9, tzinfo=UTC).isoformat()
        event = client.post(
            "/api/v1/events",
            json={
                "event_id": new_ulid(),
                "baby_id": baby_id,
                "family_id": family_id,
                "user_id": init_payload["admin_user_id"],
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

        alert = client.post(
            "/api/v1/alerts",
            json={"baby_id": baby_id, "family_id": family_id, "level": "red", "type": "triage"},
        )
        assert alert.status_code == 200
        alert_id = alert.json()["id"]
        ack = client.post(
            f"/api/v1/alerts/{alert_id}/ack",
            json={"ack_by": init_payload["admin_user_id"]},
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
                    f"version: {new_ulid()}",
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

    # Seed state snapshot in a separate transaction and validate API reads from DB mode.
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
