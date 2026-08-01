# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 17:35:00

"""MVP feeding roundtrip dev E2E substitute.

This deterministic test mirrors the Android offline feeding path without requiring a
real device: candidate -> local pending event contract -> Events API ->
Normalization -> DerivedBabyState API.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from server.app.events.domain.observation_event import ObservationEventCreate
from server.app.main import create_app
from server.app.settings import Settings


def test_mvp_feeding_dev_roundtrip_updates_state() -> None:
    app = create_app(Settings(env="test"))
    now = datetime.now(UTC).replace(microsecond=0)
    event = ObservationEventCreate(
        baby_id="baby-e2e",
        family_id="family-e2e",
        event_type="feeding",
        start_time=now,
        client_created_at=now,
        source="manual",
        payload={"amount_ml": 120},
    )

    with TestClient(app) as client:
        created = client.post("/api/v1/events", json=event.model_dump(mode="json"))
        assert created.status_code == 200

        persisted = app.state.event_repository.events[created.json()["event_id"]]
        normalized = app.state.normalization_service.normalize(persisted)
        assert normalized is not None
        app.state.state_engine.recompute(
            baby_id="baby-e2e",
            family_id="family-e2e",
            records=app.state.derived_table_store.list_by_baby("baby-e2e"),
        )

        state = client.get("/api/v1/babies/baby-e2e/state")

    assert state.status_code == 200
    assert state.json()["snapshot"]["feeding_24h_ml"] == 120
    assert state.json()["source_event_count"] == 1
