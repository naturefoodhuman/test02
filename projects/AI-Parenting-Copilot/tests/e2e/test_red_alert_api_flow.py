# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 17:36:00

"""Red alert API E2E substitute with dispatch, ack, cancel receipts, feedback."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_red_alert_api_dispatch_ack_cancel_feedback_flow() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/alerts",
            json={
                "baby_id": "baby-e2e",
                "family_id": "family-e2e",
                "level": "red",
                "type": "triage",
                "evidence": {"rule": "triage.young_infant_fever_redline"},
                "recommended_action": "open app for details",
            },
        )
        assert created.status_code == 200
        alert_id = created.json()["id"]

        dispatched = client.post(f"/api/v1/alerts/{alert_id}/dispatch")
        assert dispatched.status_code == 200
        assert {receipt["channel"] for receipt in dispatched.json()} == {
            "fcm",
            "mac_speaker",
            "app_fullscreen",
            "camera_speaker",
        }

        acked = client.post(f"/api/v1/alerts/{alert_id}/ack", json={"ack_by": "parent-1"})
        assert acked.status_code == 200
        assert acked.json()["status"] == "acknowledged"

        deliveries = client.get(f"/api/v1/alerts/{alert_id}/deliveries")
        assert deliveries.status_code == 200
        statuses = {receipt["status"] for receipt in deliveries.json()}
        assert "dry_run" in statuses or "queued" in statuses
        assert "cancelled" in statuses

        feedback = client.post(
            f"/api/v1/alerts/{alert_id}/feedback",
            json={"feedback": "useful", "note": "e2e"},
        )
        assert feedback.status_code == 200
        assert feedback.json()["feedback"]["type"] == "useful"

    audit_actions = [record.action for record in app.state.audit_sink.records]
    assert "alert.create" in audit_actions
    assert "alert.dispatch" in audit_actions
    assert "alert.ack" in audit_actions
    assert "alert.cancel_channels" in audit_actions
    assert "alert.feedback" in audit_actions
