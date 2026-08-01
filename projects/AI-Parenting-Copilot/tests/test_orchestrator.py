# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-02 01:25:00


"""APC-T028 Orchestrator dev tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.orchestrator.intent_router import IntentRouter
from server.app.orchestrator.orchestrator import Orchestrator, OrchestratorRequest
from server.app.settings import Settings


def test_intent_router_supports_required_intents() -> None:
    router = IntentRouter()

    assert router.route("刚喂了90ml奶") == "record"
    assert router.route("宝宝发烧了") == "triage"
    assert router.route("确认告警") == "alert_ack"
    assert router.route("设置提醒") == "config"


async def _handle_record() -> str:
    response = await Orchestrator().handle(OrchestratorRequest(text="刚喂了90ml奶"))
    assert response.copilot_response is not None
    return str(response.copilot_response.payload["record_candidate"])


def test_orchestrator_query_api_returns_logger_candidate() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        response = client.post("/api/v1/copilot/query", json={"text": "刚喂了90ml奶"})

    assert response.status_code == 200
    candidate = response.json()["copilot_response"]["payload"]["record_candidate"]
    assert candidate["event_type"] == "feeding"
    assert candidate["normalized_payload"]["amount_ml"] == 90.0


def test_copilot_confirm_record_candidate_writes_event_and_audit() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        confirmed = client.post(
            "/api/v1/copilot/record-candidates/confirm",
            json={
                "baby_id": "baby-1",
                "family_id": "family-1",
                "event_type": "feeding",
                "normalized_payload": {"amount_ml": 90},
                "confidence": 0.92,
                "raw_text": "刚喂了90ml奶",
            },
        )

    assert confirmed.status_code == 200
    event_id = confirmed.json()["event_id"]
    assert app.state.event_repository.events[event_id].payload == {"amount_ml": 90}
    assert app.state.audit_sink.records[-1].action == "copilot.record_confirm"


def test_copilot_confirm_family_memory_writes_knowledge_and_audit() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        confirmed = client.post(
            "/api/v1/copilot/family-memory/confirm",
            json={"family_id": "family-1", "key": "sleep.preference", "value": "white_noise"},
        )

    assert confirmed.status_code == 200
    assert confirmed.json()["family_knowledge"]["value"] == {"value": "white_noise"}
    assert app.state.audit_sink.records[-1].action == "copilot.family_memory_confirm"
