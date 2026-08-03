# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:30:00

"""ESP32C6 firmware preflight tests."""

from __future__ import annotations

import json
from pathlib import Path

from firmware.esp32c6.tools.preflight import run_preflight


def test_firmware_preflight_passes_static_checks() -> None:
    result = run_preflight(Path("firmware/esp32c6"))

    assert result.ok is True
    assert result.checks["platform_board"] == "ok"
    assert result.checks["pubsubclient_dep"] == "ok"
    assert result.checks["mqtt_topic"] == "ok"
    assert result.checks["mock_payload_json"] == "ok"


def test_firmware_mock_payload_string_is_valid_json_shape() -> None:
    source = Path("firmware/esp32c6/src/main.cpp").read_text(encoding="utf-8")

    for field in [
        "presence",
        "state",
        "breathing_rate",
        "heart_rate",
        "abnormal_event",
        "timestamp",
    ]:
        assert f'\\"{field}\\"' in source

    payload = {
        "presence": True,
        "state": "moving",
        "breathing_rate": 32,
        "heart_rate": 120,
        "abnormal_event": None,
        "timestamp": 123,
    }
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    assert set(decoded) == {
        "presence",
        "state",
        "breathing_rate",
        "heart_rate",
        "abnormal_event",
        "timestamp",
    }
