# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 22:25:00

"""Family knowledge API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_family_knowledge_upsert_list_and_audit() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/family-knowledge",
            json={
                "family_id": "family-1",
                "key": "sleep.preference",
                "value": {"value": "white_noise"},
            },
        )
        second = client.post(
            "/api/v1/family-knowledge",
            json={
                "family_id": "family-1",
                "key": "sleep.preference",
                "value": {"value": "rain"},
            },
        )
        listed = client.get("/api/v1/family-knowledge/family-1")

    assert first.status_code == 200
    assert first.json()["version"] == 1
    assert second.status_code == 200
    assert second.json()["version"] == 2
    assert listed.status_code == 200
    assert listed.json()[0]["value"] == {"value": "rain"}
    assert app.state.audit_sink.records[-1].action == "family_knowledge.upsert"
