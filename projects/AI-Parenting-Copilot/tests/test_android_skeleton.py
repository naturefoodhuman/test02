# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 11:10:00

"""APC-T045/T046/T047/T048 Android skeleton static tests."""

from __future__ import annotations

import json
from pathlib import Path

ANDROID = Path("android")


def test_android_package_is_android_only_react_native_shell() -> None:
    package = json.loads((ANDROID / "package.json").read_text())

    assert package["_forge_trace"]["created_by"] == "Arena.ai Agent Mode"
    assert "react-native" in package["dependencies"]
    assert "@powersync/react-native" in package["dependencies"]
    assert "@react-native-firebase/messaging" in package["dependencies"]
    assert "ios" not in json.dumps(package).lower()


def test_api_client_supports_base_url_and_bearer_token() -> None:
    client = (ANDROID / "src/api/client.ts").read_text()

    assert "baseUrl" in client
    assert "Bearer" in client
    assert "/healthz" in client


def test_auth_session_and_device_registration_flow_sources_exist() -> None:
    session = (ANDROID / "src/state/session.ts").read_text()
    auth = (ANDROID / "src/features/auth/authService.ts").read_text()

    assert "sessionReducer" in session
    assert "logout" in session
    assert "/api/v1/auth/login" in auth
    assert "/api/v1/auth/devices/register" in auth
    assert "fcm_token" in auth


def test_sync_schema_contains_offline_pending_contract_fields() -> None:
    schema = (ANDROID / "src/sync/schema.ts").read_text()
    store = (ANDROID / "src/sync/local_event_store.ts").read_text()

    for field in [
        "event_id",
        "baby_id",
        "family_id",
        "user_id",
        "device_id",
        "source",
        "confidence",
    ]:
        assert field in schema
    assert "pending_sync" in schema
    assert "pending_sync: true" in store


def test_quick_record_candidate_builds_feeding_payload_contract() -> None:
    candidate = (ANDROID / "src/features/quick_record/recordCandidate.ts").read_text()
    event = (ANDROID / "src/features/quick_record/createLocalEvent.ts").read_text()

    assert "amount_ml" in candidate
    assert "requiresConfirmation: true" in candidate
    assert "event_type: candidate.eventType" in event
    assert "Omit<LocalObservationEvent, 'pending_sync'>" in event
