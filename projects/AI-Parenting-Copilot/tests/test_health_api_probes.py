# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:35:00

"""System health API probe snapshot tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.health.monitor import DeviceHealthMonitor, MockHealthProbe
from server.app.main import create_app
from server.app.notification.alert_repo import InMemoryAlertRepository
from server.app.settings import Settings


def test_system_health_returns_device_probe_snapshot_and_gray_alert() -> None:
    app = create_app(Settings(env="test"))
    app.state.alert_repository = InMemoryAlertRepository()
    app.state.device_health_monitor = DeviceHealthMonitor(
        [MockHealthProbe("camera", online=False)],
        app.state.alert_repository,
    )

    with TestClient(app) as client:
        check = client.post(
            "/api/v1/system/health/check",
            params={"family_id": "family-1", "baby_id": "baby-1"},
        )
        snapshot = client.get("/api/v1/system/health")

    assert check.status_code == 200
    assert check.json()["checks"] == {"camera": "offline"}
    assert snapshot.status_code == 200
    assert snapshot.json()["status"] == "degraded"
    assert snapshot.json()["device_health"] == {"camera": "offline"}
    assert app.state.audit_sink.records[-1].action == "system.health_check"
