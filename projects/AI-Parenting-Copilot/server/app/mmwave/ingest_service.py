# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 18:10:00

"""mmWave ingest service shared by API and MQTT worker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from server.app.events.domain.observation_event import ObservationEvent
from server.app.events.infra.repository import EventRepository
from server.app.mmwave.frame_parser import RadarFrame, parse_radar_frame
from server.app.mmwave.sensor_event_mapper import (
    map_frame_to_observation_event,
    map_frame_to_sensor_event,
)
from server.app.mmwave.sqlalchemy_sensor_event_repo import SensorEventRecord


class SensorEventRepository(Protocol):
    async def add(self, record) -> SensorEventRecord:  # type: ignore[no-untyped-def]
        """Persist a sensor event candidate or record."""


@dataclass(frozen=True, slots=True)
class MMWaveIngestResult:
    sensor_event: SensorEventRecord
    observation_event: ObservationEvent | None = None


class MMWaveIngestService:
    """Process parsed or raw radar frames into SensorEvent and optional ObservationEvent."""

    async def ingest_frame(
        self,
        frame: RadarFrame,
        *,
        sensor_repo: SensorEventRepository,
        event_repo: EventRepository | None = None,
        baby_id: str | None = None,
        family_id: str | None = None,
    ) -> MMWaveIngestResult:
        sensor = await sensor_repo.add(map_frame_to_sensor_event(frame))
        observation: ObservationEvent | None = None
        if event_repo is not None and baby_id and family_id:
            observation = await event_repo.upsert(
                map_frame_to_observation_event(frame, baby_id=baby_id, family_id=family_id)
            )
        return MMWaveIngestResult(sensor_event=sensor, observation_event=observation)

    async def ingest_payload(
        self,
        topic: str,
        payload: str | bytes,
        *,
        sensor_repo: SensorEventRepository,
        event_repo: EventRepository | None = None,
        baby_id: str | None = None,
        family_id: str | None = None,
    ) -> MMWaveIngestResult:
        return await self.ingest_frame(
            parse_radar_frame(payload, topic=topic),
            sensor_repo=sensor_repo,
            event_repo=event_repo,
            baby_id=baby_id,
            family_id=family_id,
        )
