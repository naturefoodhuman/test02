# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-02 04:12:00

"""APC-T039 camera shadow pipeline tests."""

from __future__ import annotations

import pytest

from server.app.camera.clip_recorder import ClipRecorder
from server.app.camera.fusion import FusionInput, FusionStateMachine
from server.app.camera.vlm_dispatcher import VLMDispatcher
from server.app.model_gateway.client import FakeModelClient, ModelResponse


def test_fusion_requires_active_sleep_session() -> None:
    decision = FusionStateMachine().evaluate(
        FusionInput(sleep_session_active=False, mmwave_abnormal_event="apnea_candidate")
    )

    assert decision.shadow_event is False
    assert decision.reason_code == "sleep_session_not_active"


def test_mmwave_alone_is_shadow_only_and_never_red() -> None:
    decision = FusionStateMachine().evaluate(
        FusionInput(sleep_session_active=True, mmwave_abnormal_event="apnea_candidate")
    )

    assert decision.shadow_event is True
    assert decision.alert_level is None
    assert "red" not in str(decision).lower()


def test_multi_signal_generates_shadow_candidate_not_red_alert() -> None:
    decision = FusionStateMachine().evaluate(
        FusionInput(
            sleep_session_active=True,
            camera_kind="face_covered",
            camera_confidence=0.91,
            mmwave_abnormal_event="apnea_candidate",
        )
    )
    clip = ClipRecorder().plan_clip(event_id="camera-event-1")

    assert decision.shadow_event is True
    assert decision.alert_level == "shadow"
    assert clip.pre_seconds == 15
    assert clip.post_seconds == 30
    assert clip.path and clip.path.endswith("camera-event-1.mp4")


class FakeVisionClient(FakeModelClient):
    async def vision(self, **kwargs):  # type: ignore[no-untyped-def]
        self.requests.append(kwargs)  # type: ignore[arg-type]
        return ModelResponse(text="shadow ok", model="fake", provider="fake", plan_key="fake")


@pytest.mark.asyncio
async def test_vlm_dispatcher_uses_injected_model_gateway_client() -> None:
    client = FakeVisionClient()
    result = await VLMDispatcher(client).dispatch(image_base64="ZmFrZQ==", prompt="check")

    assert result.dispatched is True
    assert result.mode == "shadow"
    assert result.response_text == "shadow ok"


def test_camera_vlm_shadow_api_uses_optional_model_client() -> None:
    from fastapi.testclient import TestClient

    from server.app.main import create_app
    from server.app.settings import Settings

    app = create_app(Settings(env="test"))
    app.state.model_client = FakeVisionClient()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/camera-vlm/shadow",
            json={"image_base64": "ZmFrZQ==", "prompt": "check"},
        )

    assert response.status_code == 200
    assert response.json()["mode"] == "shadow"
    assert response.json()["dispatched"] is True
    assert response.json()["response_text"] == "shadow ok"


def test_camera_vlm_shadow_api_can_dry_run_without_model_client() -> None:
    from fastapi.testclient import TestClient

    from server.app.main import create_app
    from server.app.settings import Settings

    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/camera-vlm/shadow",
            json={"image_base64": "ZmFrZQ==", "dispatch": False},
        )

    assert response.status_code == 200
    assert response.json()["mode"] == "shadow"
    assert response.json()["dispatched"] is False


def test_camera_shadow_evaluate_api_combines_fusion_and_vlm_dry_run() -> None:
    from fastapi.testclient import TestClient

    from server.app.main import create_app
    from server.app.settings import Settings

    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/camera-shadow/evaluate",
            json={
                "camera_id": "camera-dev",
                "session_id": "sleep-1",
                "sleep_session_active": True,
                "camera_kind": "face_covered",
                "camera_confidence": 0.91,
                "mmwave_abnormal_event": "apnea_candidate",
                "image_base64": "ZmFrZQ==",
                "dispatch_vlm": False,
            },
        )

    assert response.status_code == 200
    assert response.json()["decision"]["reason_code"] == "multi_signal_shadow_candidate"
    assert response.json()["camera_event"]["kind"] == "face_covered"
    assert response.json()["vlm"] == {
        "mode": "shadow",
        "dispatched": False,
        "response_text": None,
    }
