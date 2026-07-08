# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 04:25:00


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
