# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:55:00


"""MQTT subscriber skeleton for mmWave frames.

The real network loop requires Mosquitto and is validated in integration. This module
keeps parsing/mapping testable without connecting to MQTT in CI.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from server.app.mmwave.frame_parser import parse_radar_frame
from server.app.mmwave.sensor_event_mapper import SensorEventCandidate, map_frame_to_sensor_event

FrameHandler = Callable[[SensorEventCandidate], Awaitable[None]]


@dataclass(slots=True)
class MQTTSubscriberConfig:
    host: str = "127.0.0.1"
    port: int = 1883
    topics: list[str] = field(default_factory=lambda: ["baby/radar/telemetry"])
    reconnect_backoff_seconds: float = 1.0


class MMWaveMQTTSubscriber:
    def __init__(self, config: MQTTSubscriberConfig, handler: FrameHandler) -> None:
        self.config = config
        self.handler = handler

    def topic_allowed(self, topic: str) -> bool:
        return topic in self.config.topics

    async def handle_message(self, topic: str, payload: str | bytes) -> SensorEventCandidate:
        if not self.topic_allowed(topic):
            raise ValueError(f"topic not allowed: {topic}")
        candidate = map_frame_to_sensor_event(parse_radar_frame(payload, topic=topic))
        await self.handler(candidate)
        return candidate
