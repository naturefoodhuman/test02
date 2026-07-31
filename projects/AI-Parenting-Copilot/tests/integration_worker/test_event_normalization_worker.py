# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 21:18:00

"""Live PG LISTEN/NOTIFY worker smoke for event -> normalization -> state.

This test is intentionally separated from `tests/integration/` so the regular
DB repository suite stays fast and deterministic. Run it with
`make worker-db-smoke-test` when PostgreSQL is available.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from server.app.common.ids import new_ulid
from server.app.db import normalize_database_url
from server.app.main import create_app

pytestmark = pytest.mark.integration


def _db_url() -> str:
    url = os.getenv("PARENTING_DATABASE__URL") or os.getenv("PARENTING_DATABASE_URL")
    if not url:
        pytest.skip("PARENTING_DATABASE__URL not set; skipping worker DB smoke test")
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


async def _seed_family_baby(engine: AsyncEngine, family_id: str, baby_id: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text("INSERT INTO family (id, name, timezone) VALUES (:id, :name, :timezone)"),
            {"id": family_id, "name": "Worker Smoke Family", "timezone": "Asia/Shanghai"},
        )
        await connection.execute(
            text("INSERT INTO baby (id, family_id, name) VALUES (:id, :family_id, :name)"),
            {"id": baby_id, "family_id": family_id, "name": "Worker Smoke Baby"},
        )


async def _cleanup_family(engine: AsyncEngine, family_id: str) -> None:
    async with engine.begin() as connection:
        for statement in [
            "DELETE FROM derived_baby_state WHERE family_id = :family_id",
            "DELETE FROM feeding_log WHERE family_id = :family_id",
            "DELETE FROM diaper_log WHERE family_id = :family_id",
            "DELETE FROM sleep_log WHERE family_id = :family_id",
            "DELETE FROM temperature_log WHERE family_id = :family_id",
            "DELETE FROM supplement_log WHERE family_id = :family_id",
            "DELETE FROM observation_event WHERE family_id = :family_id",
            "DELETE FROM baby WHERE family_id = :family_id",
            "DELETE FROM family WHERE id = :family_id",
        ]:
            await connection.execute(text(statement), {"family_id": family_id})


async def _event_processing_status(engine: AsyncEngine, event_id: str) -> str | None:
    async with engine.connect() as connection:
        return await connection.scalar(
            text("SELECT processing_status FROM observation_event WHERE event_id = :event_id"),
            {"event_id": event_id},
        )


@pytest.mark.asyncio
async def test_postgres_worker_processes_notify_into_state(engine: AsyncEngine) -> None:
    family_id = new_ulid()
    baby_id = new_ulid()
    event_id = new_ulid()
    await _seed_family_baby(engine, family_id, baby_id)
    try:
        app = create_app()
        with TestClient(app) as client:
            now = datetime(2026, 7, 31, 9, 0, tzinfo=UTC).isoformat()
            created = client.post(
                "/api/v1/events",
                json={
                    "event_id": event_id,
                    "baby_id": baby_id,
                    "family_id": family_id,
                    "event_type": "feeding",
                    "start_time": now,
                    "client_created_at": now,
                    "source": "manual",
                    "payload": {"amount_ml": 111},
                },
            )
            assert created.status_code == 200

            state_payload: dict[str, object] | None = None
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                state = client.get(f"/api/v1/babies/{baby_id}/state")
                if state.status_code == 200:
                    payload = state.json()
                    if payload["snapshot"].get("feeding_24h_ml") == 111:
                        state_payload = payload
                        break
                time.sleep(0.1)

            assert state_payload is not None
            assert state_payload["source_event_count"] == 1

        assert await _event_processing_status(engine, event_id) == "normalized"
    finally:
        await _cleanup_family(engine, family_id)
