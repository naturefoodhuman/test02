# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:05:00


"""APC-T010 Events API dev/in-memory integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def _payload() -> dict[str, object]:
    now = datetime(2026, 7, 9, tzinfo=UTC).isoformat()
    return {
        "event_id": "01KX15EVENT00000000000000",
        "baby_id": "baby-1",
        "family_id": "family-1",
        "event_type": "feeding",
        "start_time": now,
        "client_created_at": now,
        "source": "manual",
        "payload": {"amount_ml": 90},
    }


def test_events_api_create_list_correct_delete_flow_records_audit() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        created = client.post("/api/v1/events", json=_payload())
        assert created.status_code == 200

        repeated = client.post("/api/v1/events", json=_payload())
        assert repeated.status_code == 200
        assert repeated.json()["event_id"] == created.json()["event_id"]

        listed = client.get("/api/v1/events", params={"baby_id": "baby-1"})
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        corrected = client.post(
            f"/api/v1/events/{created.json()['event_id']}/correct",
            json={"normalized_payload": {"amount_ml": 100}},
        )
        assert corrected.status_code == 200
        assert corrected.json()["correction_of"] == created.json()["event_id"]

        deleted = client.delete(f"/api/v1/events/{created.json()['event_id']}")
        assert deleted.status_code == 200
        assert deleted.json()["is_deleted"] is True

    audit_sink = app.state.audit_sink
    assert [record.action for record in audit_sink.records] == [
        "event.upsert",
        "event.upsert",
        "event.correct",
        "event.soft_delete",
    ]
