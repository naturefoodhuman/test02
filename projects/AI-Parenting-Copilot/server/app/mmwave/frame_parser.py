# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:55:00


"""mmWave radar frame parser for JSON MQTT payloads."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


class RadarFrame(BaseModel):
    device_id: str = "mmwave-dev"
    topic: str = "baby/radar/telemetry"
    timestamp: str
    presence: bool = False
    state: str = "unknown"
    breathing_rate: float | None = Field(default=None, ge=0)
    heart_rate: float | None = Field(default=None, ge=0)
    abnormal_event: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


def parse_radar_frame(payload: str | bytes, *, topic: str = "baby/radar/telemetry") -> RadarFrame:
    """Parse a JSON radar frame from MQTT payload text/bytes."""

    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("radar frame payload must be a JSON object")
    return RadarFrame(
        device_id=str(data.get("device_id", "mmwave-dev")),
        topic=topic,
        timestamp=str(data["timestamp"]),
        presence=bool(data.get("presence", False)),
        state=str(data.get("state", "unknown")),
        breathing_rate=data.get("breathing_rate"),
        heart_rate=data.get("heart_rate"),
        abnormal_event=data.get("abnormal_event"),
        raw=dict(data),
    )


def parse_jsonl(text: str, *, topic: str = "baby/radar/telemetry") -> list[RadarFrame]:
    """Parse newline-delimited radar frame fixtures."""

    return [parse_radar_frame(line, topic=topic) for line in text.splitlines() if line.strip()]
