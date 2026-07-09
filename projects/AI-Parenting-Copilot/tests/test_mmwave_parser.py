# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 07:55:00

"""APC-T040 mmWave parser/mapper/subscriber tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.app.mmwave.frame_parser import parse_jsonl, parse_radar_frame
from server.app.mmwave.mqtt_subscriber import MMWaveMQTTSubscriber, MQTTSubscriberConfig
from server.app.mmwave.sensor_event_mapper import (
    map_frame_to_observation_event,
    map_frame_to_sensor_event,
)


def test_parse_radar_frame_fixture_and_map_sensor_event() -> None:
    frames = parse_jsonl(Path("tests/fixtures/radar_frames.jsonl").read_text())
    sensor = map_frame_to_sensor_event(frames[1])

    assert len(frames) == 2
    assert frames[1].abnormal_event == "apnea_candidate"
    assert sensor.signal_type == "apnea_candidate"
    assert sensor.payload["breathing_rate"] == 0


def test_map_frame_to_observation_event_candidate() -> None:
    frame = parse_radar_frame(
        '{"timestamp":"2026-07-09T00:00:00Z","presence":true,"state":"moving"}'
    )

    event = map_frame_to_observation_event(frame, baby_id="baby-1", family_id="family-1")

    assert event.source == "sensor"
    assert event.event_type == "mmwave_telemetry"
    assert event.normalized_payload["presence"] is True


@pytest.mark.asyncio
async def test_mqtt_subscriber_topic_whitelist_and_handler() -> None:
    seen = []

    async def handler(candidate):  # type: ignore[no-untyped-def]
        seen.append(candidate)

    subscriber = MMWaveMQTTSubscriber(
        MQTTSubscriberConfig(topics=["baby/radar/telemetry"]),
        handler,
    )
    candidate = await subscriber.handle_message(
        "baby/radar/telemetry",
        b'{"timestamp":"2026-07-09T00:00:00Z","presence":false,"state":"empty"}',
    )

    assert candidate.signal_type == "empty"
    assert seen == [candidate]
    assert not subscriber.topic_allowed("other/topic")
