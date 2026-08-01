# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 16:42:00

"""mmWave frame API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_mmwave_frame_ingest_api_returns_sensor_event_candidate() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/mmwave/frames",
            json={
                "topic": "baby/radar/telemetry",
                "frame": {
                    "device_id": "mmwave-dev",
                    "timestamp": "2026-08-01T00:00:00Z",
                    "presence": True,
                    "state": "moving",
                    "abnormal_event": "apnea_candidate",
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sensor_event"]["device_id"] == "mmwave-dev"
    assert payload["sensor_event"]["signal_type"] == "apnea_candidate"
    assert payload["observation_event_id"] is None

    with TestClient(app) as client:
        listed = client.get("/api/v1/mmwave/devices/mmwave-dev/events")

    assert listed.status_code == 200
    assert listed.json()[0]["signal_type"] == "apnea_candidate"
