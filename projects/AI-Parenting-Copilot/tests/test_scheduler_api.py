# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 11:25:00

"""Scheduler API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_scheduler_api_lists_and_triggers_jobs_with_audit() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        jobs = client.get("/api/v1/scheduler/jobs")
        morning = client.post("/api/v1/scheduler/jobs/morning_brief/trigger")
        all_jobs = client.post("/api/v1/scheduler/trigger-all")

    assert jobs.status_code == 200
    assert {"health_check", "morning_brief", "supplement", "vaccine_due"}.issubset(
        set(jobs.json())
    )
    assert morning.status_code == 200
    assert morning.json()["kind"] == "morning_brief"
    assert all_jobs.status_code == 200
    assert "health_check" in all_jobs.json()
    audit_actions = [record.action for record in app.state.audit_sink.records]
    assert "scheduler.trigger" in audit_actions
    assert "scheduler.trigger_all" in audit_actions


def test_scheduler_api_unknown_job_returns_404() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        response = client.post("/api/v1/scheduler/jobs/not-a-job/trigger")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
