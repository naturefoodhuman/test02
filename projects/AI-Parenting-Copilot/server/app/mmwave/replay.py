# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:45:00

"""mmWave fixture replay report for MQTT/device integration dry-runs."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from server.app.mmwave.frame_parser import RadarFrame, parse_jsonl
from server.app.mmwave.sensor_event_mapper import (
    map_frame_to_observation_event,
    map_frame_to_sensor_event,
)


@dataclass(frozen=True, slots=True)
class MMWaveReplayFrameResult:
    index: int
    device_id: str
    timestamp: str
    signal_type: str
    presence: bool
    observation_event_type: str | None = None


@dataclass(frozen=True, slots=True)
class MMWaveReplayReport:
    fixture: str
    topic: str
    total_frames: int
    abnormal_count: int
    presence_count: int
    signal_type_counts: dict[str, int]
    observation_count: int
    frames: tuple[MMWaveReplayFrameResult, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def replay_mmwave_fixture(
    fixture: Path | str,
    *,
    topic: str = "baby/radar/telemetry",
    baby_id: str | None = "baby-replay",
    family_id: str | None = "family-replay",
) -> MMWaveReplayReport:
    path = Path(fixture)
    frames = parse_jsonl(path.read_text(encoding="utf-8"), topic=topic)
    results = tuple(
        _frame_result(index, frame, baby_id=baby_id, family_id=family_id)
        for index, frame in enumerate(frames)
    )
    signal_counts = Counter(result.signal_type for result in results)
    return MMWaveReplayReport(
        fixture=str(path),
        topic=topic,
        total_frames=len(frames),
        abnormal_count=sum(1 for frame in frames if frame.abnormal_event),
        presence_count=sum(1 for frame in frames if frame.presence),
        signal_type_counts=dict(signal_counts),
        observation_count=sum(1 for result in results if result.observation_event_type is not None),
        frames=results,
    )


def _frame_result(
    index: int,
    frame: RadarFrame,
    *,
    baby_id: str | None,
    family_id: str | None,
) -> MMWaveReplayFrameResult:
    sensor = map_frame_to_sensor_event(frame)
    observation_type: str | None = None
    if baby_id and family_id:
        observation = map_frame_to_observation_event(frame, baby_id=baby_id, family_id=family_id)
        observation_type = observation.event_type
    return MMWaveReplayFrameResult(
        index=index,
        device_id=frame.device_id,
        timestamp=frame.timestamp,
        signal_type=sensor.signal_type,
        presence=frame.presence,
        observation_event_type=observation_type,
    )
