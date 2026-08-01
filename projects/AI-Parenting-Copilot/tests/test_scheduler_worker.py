# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:20:00

"""Periodic scheduler worker tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.scheduler.jobs.morning_brief import MorningBriefJob
from server.app.scheduler.runner import SchedulerRunner
from server.app.scheduler.worker import PeriodicSchedulerWorker
from server.app.settings import Settings


@pytest.mark.asyncio
async def test_periodic_scheduler_worker_run_once_records_snapshot() -> None:
    runner = SchedulerRunner()
    runner.register(MorningBriefJob())
    worker = PeriodicSchedulerWorker(runner, interval_seconds=9999)

    result = await worker.run_once()

    assert result["morning_brief"]["kind"] == "morning_brief"
    assert worker.snapshot.run_count == 1
    assert worker.snapshot.last_finished_at is not None
    assert worker.snapshot.last_error is None


def test_fastapi_lifespan_registers_scheduler_worker() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        health = client.get("/api/v1/system/health")

    assert health.status_code == 200
    assert any(
        worker.name == "scheduler-periodic-worker"
        for worker in app.state.container.worker_registry.workers
    )
