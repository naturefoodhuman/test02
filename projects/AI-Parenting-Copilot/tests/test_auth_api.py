# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 01:15:00


"""APC-T008 Auth API integration tests in dev/in-memory mode."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_init_family_login_me_and_device_registration_flow() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        init_response = client.post(
            "/api/v1/auth/init-family",
            json={
                "family_name": "Test Family",
                "admin_display_name": "Mom",
                "admin_secret": "secret123",
            },
        )
        assert init_response.status_code == 200
        init_payload = init_response.json()

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "family_id": init_payload["family_id"],
                "display_name": "Mom",
                "secret": "secret123",
                "device_id": "phone-local",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        me_response = client.get("/api/v1/auth/me", headers={"authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        assert me_response.json()["role"] == "Admin"

        device_response = client.post(
            "/api/v1/auth/devices/register",
            headers={"authorization": f"Bearer {token}"},
            json={"kind": "phone", "name": "Mom phone", "fcm_token": "fake-fcm"},
        )
        assert device_response.status_code == 200
        assert device_response.json()["kind"] == "phone"


def test_auth_me_requires_bearer_token() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
