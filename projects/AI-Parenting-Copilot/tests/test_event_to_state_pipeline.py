# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""APC-T017 event -> normalization -> state integration test."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from server.app.events.domain.observation_event import EventSource, ObservationEventCreate
from server.app.main import create_app
from server.app.settings import Settings


def test_event_to_normalization_to_state_dev_pipeline() -> None:
    app = create_app(Settings(env="test"))
    now = datetime(2026, 7, 9, tzinfo=UTC)
    event = ObservationEventCreate(
        baby_id="baby-1",
        family_id="family-1",
        event_type="feeding",
        start_time=now,
        client_created_at=now,
        source=EventSource.MANUAL,
        payload={"amount_ml": 120},
    )
    with TestClient(app) as client:
        response = client.post("/api/v1/events", json=event.model_dump(mode="json"))
        assert response.status_code == 200

        persisted = app.state.event_repository.events[event.event_id]
        record = app.state.normalization_service.normalize(persisted)
        snapshot = app.state.state_engine.recompute(
            baby_id="baby-1",
            family_id="family-1",
            records=app.state.derived_table_store.list_by_baby("baby-1"),
        )
        state = client.get("/api/v1/babies/baby-1/state")

    assert record is not None
    assert snapshot.snapshot["feeding_24h_ml"] == 120
    assert state.status_code == 200
    assert state.json()["snapshot"]["feeding_24h_ml"] == 120
