# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 09:20:00


"""APC-T041 firmware skeleton tests."""

from __future__ import annotations

from pathlib import Path


def test_firmware_files_define_required_payload_fields_without_real_secrets() -> None:
    src = Path("firmware/esp32c6/src/main.cpp").read_text()
    config = Path("firmware/esp32c6/config.h.example").read_text()

    for field in [
        "presence",
        "state",
        "breathing_rate",
        "heart_rate",
        "abnormal_event",
        "timestamp",
    ]:
        assert field in src
    assert "PubSubClient" in Path("firmware/esp32c6/platformio.ini").read_text()
    assert "replace-with-local-password" in config
    assert "naturist" not in config.lower()
