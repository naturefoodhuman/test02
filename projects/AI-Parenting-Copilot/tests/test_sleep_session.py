# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:15:00

"""APC-T037 sleep session state machine/API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app.camera.roi import ROIConfig
from server.app.camera.sleep_session import InMemorySleepSessionRepository, SleepSessionState
from server.app.common.errors import ConflictError
from server.app.main import create_app
from server.app.settings import Settings


@pytest.mark.asyncio
async def test_sleep_session_state_machine_and_roi() -> None:
    repo = InMemorySleepSessionRepository()
    session = await repo.start(baby_id="baby-1", family_id="family-1")
    assert session.state == SleepSessionState.ACTIVE
    assert session.analysis_allowed is True

    paused = await repo.pause(session.id)
    assert paused.analysis_allowed is False
    with pytest.raises(ConflictError):
        await repo.pause(session.id)

    resumed = await repo.resume(session.id)
    assert resumed.analysis_allowed is True
    updated = await repo.set_roi(session.id, ROIConfig(x=0.1, y=0.2, width=0.5, height=0.4))
    assert updated.roi_config == {"x": 0.1, "y": 0.2, "width": 0.5, "height": 0.4}
    ended = await repo.end(session.id)
    assert ended.state == SleepSessionState.ENDED
    assert ended.analysis_allowed is False


def test_sleep_session_api_flow() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        start = client.post(
            "/api/v1/sleep-sessions",
            json={"baby_id": "baby-1", "family_id": "family-1"},
        )
        assert start.status_code == 200
        session_id = start.json()["id"]
        assert start.json()["state"] == "active"

        roi = client.put(
            f"/api/v1/sleep-sessions/{session_id}/roi",
            json={"x": 0.1, "y": 0.2, "width": 0.5, "height": 0.4},
        )
        assert roi.status_code == 200
        assert roi.json()["roi_config"]["width"] == 0.5

        pause = client.post(f"/api/v1/sleep-sessions/{session_id}/pause")
        assert pause.json()["state"] == "paused"
        resume = client.post(f"/api/v1/sleep-sessions/{session_id}/resume")
        assert resume.json()["state"] == "active"
        end = client.post(f"/api/v1/sleep-sessions/{session_id}/end")
        assert end.json()["state"] == "ended"
