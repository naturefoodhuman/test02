# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-02 05:15:00

"""APC-T038 camera adapter mock tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from server.app.camera.fregata_bridge import FregataBridge
from server.app.camera.isapi_client import ISAPIClient
from server.app.camera.rtsp_client import MockRTSPSnapshotClient
from server.app.main import create_app
from server.app.settings import Settings


def test_devices_yaml_camera_mock_config() -> None:
    config = yaml.safe_load(Path("config/devices.yaml").read_text())

    assert config["cameras"]["nursery"]["mode"] == "mock"
    assert config["cameras"]["nursery"]["snapshot_timeout_seconds"] == 5
    assert "baby/radar/telemetry" in config["mmwave"]["mqtt_topics"]


class FakeHTTPResponse:
    def __init__(self, status_code: int = 200, payload: dict[str, object] | None = None) -> None:
        self.status_code = status_code
        self.payload = payload or {}

    def json(self) -> dict[str, object]:
        return self.payload


class FakeCameraHTTPClient:
    def __init__(self, response: FakeHTTPResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def get(self, url: str, **kwargs: object) -> FakeHTTPResponse:
        self.calls.append(("GET", url))
        return self.response

    async def post(self, url: str, **kwargs: object) -> FakeHTTPResponse:
        self.calls.append(("POST", url))
        return self.response


@pytest.mark.asyncio
async def test_mock_rtsp_snapshot_client_returns_png() -> None:
    snapshot = await MockRTSPSnapshotClient("nursery").snapshot()

    assert snapshot.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_isapi_client_health_uses_injected_http_client() -> None:
    fake = FakeCameraHTTPClient(FakeHTTPResponse(status_code=200))
    result = await ISAPIClient("http://camera.local", http_client=fake).health()

    assert result["status"] == "online"
    assert result["http_status"] == "200"
    assert fake.calls == [("GET", "http://camera.local/ISAPI/System/status")]


@pytest.mark.asyncio
async def test_fregata_bridge_normalizes_shadow_events() -> None:
    fake = FakeCameraHTTPClient(
        FakeHTTPResponse(
            status_code=200,
            payload={"events": [{"kind": "face_covered", "confidence": 0.91}]},
        )
    )
    result = await FregataBridge("http://fregata.local/analyze", http_client=fake).analyze_snapshot(
        b"jpeg"
    )

    assert result["mode"] == "shadow"
    assert result["source"] == "fregata"
    assert result["events"] == [{"kind": "face_covered", "confidence": 0.91}]
    assert fake.calls == [("POST", "http://fregata.local/analyze")]


def test_camera_snapshot_api_returns_png() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        response = client.get("/api/v1/cameras/nursery/snapshot")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_camera_event_api_dev_store_by_session() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/camera-events",
            json={
                "camera_id": "camera-dev",
                "session_id": "sleep-1",
                "ts": "2026-08-01T00:00:00Z",
                "kind": "face_covered",
                "confidence": 0.91,
            },
        )
        listed = client.get("/api/v1/sleep-sessions/sleep-1/camera-events")

    assert created.status_code == 200
    assert created.json()["kind"] == "face_covered"
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == created.json()["id"]


def test_camera_fusion_api_creates_shadow_camera_event() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        fused = client.post(
            "/api/v1/camera-fusion/evaluate",
            json={
                "camera_id": "camera-dev",
                "session_id": "sleep-1",
                "sleep_session_active": True,
                "camera_kind": "face_covered",
                "camera_confidence": 0.91,
                "mmwave_abnormal_event": "apnea_candidate",
            },
        )
        listed = client.get("/api/v1/sleep-sessions/sleep-1/camera-events")

    summary = client.get("/api/v1/sleep-sessions/sleep-1/shadow-summary")

    assert fused.status_code == 200
    assert fused.json()["decision"]["reason_code"] == "multi_signal_shadow_candidate"
    assert fused.json()["clip_plan"]["path"].endswith("sleep-1.mp4")
    assert fused.json()["camera_event"]["kind"] == "face_covered"
    assert listed.json()[0]["id"] == fused.json()["camera_event"]["id"]
    assert summary.status_code == 200
    assert summary.json()["shadow_count"] == 1
    assert summary.json()["clip_paths"][0].endswith("sleep-1.mp4")
