# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 21:10:00

"""Sync state API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_sync_heartbeat_records_pending_count_and_audit() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        heartbeat = client.post(
            "/api/v1/sync/heartbeat",
            json={"client_id": "android-1", "family_id": "family-1", "pending_count": 3},
        )
        loaded = client.get("/api/v1/sync/state/android-1")

    assert heartbeat.status_code == 200
    assert heartbeat.json()["pending_count"] == 3
    assert loaded.status_code == 200
    assert loaded.json()["family_id"] == "family-1"
    assert app.state.audit_sink.records[-1].action == "sync.heartbeat"
