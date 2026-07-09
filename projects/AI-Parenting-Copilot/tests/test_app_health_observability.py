# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 22:55:00


"""APC-T002/T005 integration tests for app shell and observability."""

from __future__ import annotations

import structlog
from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.observability.logger import mask_sensitive
from server.app.settings import ObservabilitySettings, Settings


def test_healthz_and_openapi_available_without_db() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        health = client.get("/healthz")
        openapi = client.get("/openapi.json")

    assert health.status_code == 200
    assert health.json()["dependencies"]["database"]["mode"] == "dev-mock"
    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"] == "AI Parenting Copilot"


def test_metrics_endpoint_returns_prometheus_format() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        client.get("/healthz")
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "parenting_http_requests_total" in response.text
    assert "parenting_registered_workers" in response.text


def test_request_logging_binds_request_id() -> None:
    settings = Settings(
        env="test",
        observability=ObservabilitySettings(json_logs=False, tracing_enabled=False),
    )
    app = create_app(settings)
    with structlog.testing.capture_logs() as captured:
        with TestClient(app) as client:
            response = client.get("/healthz", headers={"x-request-id": "req-123"})

    assert response.headers["x-request-id"] == "req-123"
    assert any(log.get("request_id") == "req-123" for log in captured)
    assert any(log.get("event") == "http_request" for log in captured)


def test_mask_sensitive_recursively_masks_pii() -> None:
    payload = {
        "raw_input": "baby note",
        "nested": {
            "email": "parent@example.com",
            "media_path": "/private/baby/video.mp4",
            "message": "call +1 555 123 4567",
        },
    }

    masked = mask_sensitive(payload)

    assert masked["raw_input"] == "***MASKED***"
    assert masked["nested"]["media_path"] == "***MASKED***"
    assert masked["nested"]["email"] == "***EMAIL***"
    assert masked["nested"]["message"] == "call ***PHONE***"
