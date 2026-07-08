# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 05:55:00

"""APC-T031 Alert API dev tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_alert_create_list_ack_feedback_with_audit() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/alerts",
            json={
                "baby_id": "baby-1",
                "family_id": "family-1",
                "level": "red",
                "type": "triage",
                "evidence": {"rule": "triage.young_infant_fever_redline"},
            },
        )
        assert created.status_code == 200
        alert_id = created.json()["id"]

        listed = client.get("/api/v1/alerts", params={"family_id": "family-1"})
        assert listed.status_code == 200
        assert listed.json()[0]["id"] == alert_id

        acked = client.post(
            f"/api/v1/alerts/{alert_id}/ack",
            json={"ack_by": "u1", "device_id": "d1"},
        )
        assert acked.status_code == 200
        assert acked.json()["status"] == "acknowledged"

        feedback = client.post(
            f"/api/v1/alerts/{alert_id}/feedback",
            json={"feedback": "false_positive", "note": "too sensitive"},
        )
        assert feedback.status_code == 200
        assert feedback.json()["feedback"]["type"] == "false_positive"

    assert [record.action for record in app.state.audit_sink.records] == [
        "alert.create",
        "alert.ack",
        "alert.feedback",
    ]
