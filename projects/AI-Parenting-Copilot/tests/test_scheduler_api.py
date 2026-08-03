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


def test_scheduler_trigger_can_create_blue_reminder_alert() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        triggered = client.post(
            "/api/v1/scheduler/jobs/vaccine_due/trigger",
            params={
                "family_id": "family-1",
                "baby_id": "baby-1",
                "create_alert": True,
            },
        )
        alerts = client.get("/api/v1/alerts", params={"family_id": "family-1"})

    assert triggered.status_code == 200
    assert triggered.json()["alert_level"] == "blue"
    alert_id = triggered.json()["created_alert_id"]
    assert alerts.status_code == 200
    assert alerts.json()[0]["id"] == alert_id
    assert alerts.json()[0]["type"] == "scheduler.vaccine_due"
    assert alerts.json()[0]["recommended_action"].startswith("查看疫苗到期提醒")
    audit_actions = [record.action for record in app.state.audit_sink.records]
    assert "alert.create" in audit_actions
    assert "scheduler.trigger" in audit_actions


def test_scheduler_api_unknown_job_returns_404() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        response = client.post("/api/v1/scheduler/jobs/not-a-job/trigger")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
