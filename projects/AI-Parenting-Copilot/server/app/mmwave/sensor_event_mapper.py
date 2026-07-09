# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 07:55:00


"""Map parsed mmWave frames into SensorEvent / ObservationEvent candidates."""

from __future__ import annotations

from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.events.domain.observation_event import EventSource, ObservationEventCreate
from server.app.mmwave.frame_parser import RadarFrame


class SensorEventCandidate(BaseModel):
    device_id: str
    ts: str
    signal_type: str
    payload: dict[str, object] = Field(default_factory=dict)
    health_status: str = "online"


def map_frame_to_sensor_event(frame: RadarFrame) -> SensorEventCandidate:
    signal_type = frame.abnormal_event or frame.state or "telemetry"
    return SensorEventCandidate(
        device_id=frame.device_id,
        ts=frame.timestamp,
        signal_type=signal_type,
        payload={
            "presence": frame.presence,
            "state": frame.state,
            "breathing_rate": frame.breathing_rate,
            "heart_rate": frame.heart_rate,
            "abnormal_event": frame.abnormal_event,
            "topic": frame.topic,
        },
    )


def map_frame_to_observation_event(
    frame: RadarFrame,
    *,
    baby_id: str,
    family_id: str,
) -> ObservationEventCreate:
    """Create a sensor ObservationEvent candidate; DB write is a later task."""

    sensor = map_frame_to_sensor_event(frame)
    now = utc_now()
    return ObservationEventCreate(
        baby_id=baby_id,
        family_id=family_id,
        device_id=frame.device_id,
        event_type="mmwave_telemetry",
        start_time=now,
        client_created_at=now,
        source=EventSource.SENSOR,
        raw_input=frame.raw,
        normalized_payload={**sensor.payload, "signal_type": sensor.signal_type},
        payload=sensor.model_dump(mode="json"),
        confidence=0.8 if frame.presence else 0.5,
    )
