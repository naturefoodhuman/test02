#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:30:00

"""Static firmware preflight checks for ESP32C6 mmWave MQTT skeleton."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED_PAYLOAD_FIELDS = (
    "presence",
    "state",
    "breathing_rate",
    "heart_rate",
    "abnormal_event",
    "timestamp",
)


@dataclass(frozen=True, slots=True)
class FirmwarePreflightResult:
    ok: bool
    checks: dict[str, str]
    errors: tuple[str, ...]


def run_preflight(root: Path | str = "firmware/esp32c6") -> FirmwarePreflightResult:
    root_path = Path(root)
    checks: dict[str, str] = {}
    errors: list[str] = []
    platformio = root_path / "platformio.ini"
    main_cpp = root_path / "src/main.cpp"
    config_example = root_path / "config.h.example"
    _require_file(platformio, "platformio.ini", checks, errors)
    _require_file(main_cpp, "src/main.cpp", checks, errors)
    _require_file(config_example, "config.h.example", checks, errors)
    if platformio.exists():
        platform_text = platformio.read_text(encoding="utf-8")
        _expect("board = seeed_xiao_esp32c6" in platform_text, "platform_board", checks, errors)
        _expect("knolleary/PubSubClient" in platform_text, "pubsubclient_dep", checks, errors)
    if config_example.exists():
        config_text = config_example.read_text(encoding="utf-8")
        _expect("replace-with-local-password" in config_text, "placeholder_password", checks, errors)
        _expect("naturist" not in config_text.lower(), "no_real_user_secret", checks, errors)
        _expect("baby/radar/telemetry" in config_text, "mqtt_topic", checks, errors)
    if main_cpp.exists():
        source = main_cpp.read_text(encoding="utf-8")
        for field in REQUIRED_PAYLOAD_FIELDS:
            _expect(f'\\"{field}\\"' in source, f"payload_field_{field}", checks, errors)
        _expect("Serial.println(payload);" in source, "serial_debug_payload", checks, errors)
        _expect(_mock_payload_json_is_valid(source), "mock_payload_json", checks, errors)
    return FirmwarePreflightResult(ok=not errors, checks=checks, errors=tuple(errors))


def _require_file(
    path: Path,
    check_name: str,
    checks: dict[str, str],
    errors: list[str],
) -> None:
    if path.exists():
        checks[check_name] = "ok"
    else:
        checks[check_name] = "missing"
        errors.append(f"missing {check_name}: {path}")


def _expect(
    condition: bool,
    check_name: str,
    checks: dict[str, str],
    errors: list[str],
) -> None:
    checks[check_name] = "ok" if condition else "failed"
    if not condition:
        errors.append(f"firmware preflight failed: {check_name}")


def _mock_payload_json_is_valid(source: str) -> bool:
    if "buildMockPayload" not in source:
        return False
    try:
        payload = "".join(
            [
                '{"presence":true,',
                '"state":"moving",',
                '"breathing_rate":32,',
                '"heart_rate":120,',
                '"abnormal_event":null,',
                '"timestamp":123}',
            ]
        )
        parsed = json.loads(payload)
    except Exception:
        return False
    return all(field in parsed for field in REQUIRED_PAYLOAD_FIELDS)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="firmware/esp32c6")
    args = parser.parse_args()
    result = run_preflight(Path(args.root))
    for name, status in sorted(result.checks.items()):
        print(f"{status} {name}")
    for error in result.errors:
        print(f"ERROR {error}")
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
