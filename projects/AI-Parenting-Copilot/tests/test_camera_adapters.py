# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:15:00

"""APC-T038 camera adapter mock tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from server.app.camera.rtsp_client import MockRTSPSnapshotClient
from server.app.main import create_app
from server.app.settings import Settings


def test_devices_yaml_camera_mock_config() -> None:
    config = yaml.safe_load(Path("config/devices.yaml").read_text())

    assert config["cameras"]["nursery"]["mode"] == "mock"
    assert config["cameras"]["nursery"]["snapshot_timeout_seconds"] == 5
    assert "baby/radar/telemetry" in config["mmwave"]["mqtt_topics"]


@pytest.mark.asyncio
async def test_mock_rtsp_snapshot_client_returns_png() -> None:
    snapshot = await MockRTSPSnapshotClient("nursery").snapshot()

    assert snapshot.startswith(b"\x89PNG")


def test_camera_snapshot_api_returns_png() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        response = client.get("/api/v1/cameras/nursery/snapshot")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")
