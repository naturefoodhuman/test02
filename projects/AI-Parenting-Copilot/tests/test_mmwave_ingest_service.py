# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 18:15:00

"""mmWave ingest service/worker unit tests."""

from __future__ import annotations

import pytest

from server.app.events.domain.observation_event import ObservationEvent
from server.app.mmwave.ingest_service import MMWaveIngestService
from server.app.mmwave.sqlalchemy_sensor_event_repo import SensorEventRecord
from server.app.mmwave.worker import MMWaveMQTTWorkerConfig, MMWaveMQTTWorkerSnapshot


class _SensorRepo:
    def __init__(self) -> None:
        self.records: list[SensorEventRecord] = []

    async def add(self, record) -> SensorEventRecord:  # type: ignore[no-untyped-def]
        if not isinstance(record, SensorEventRecord):
            record = SensorEventRecord(
                device_id=record.device_id,
                ts=record.ts,
                signal_type=record.signal_type,
                payload=record.payload,
            )
        self.records.append(record)
        return record


class _EventRepo:
    def __init__(self) -> None:
        self.events: list[ObservationEvent] = []

    async def upsert(self, event) -> ObservationEvent:  # type: ignore[no-untyped-def]
        domain = ObservationEvent.model_validate(event.model_dump())
        self.events.append(domain)
        return domain


@pytest.mark.asyncio
async def test_ingest_payload_persists_sensor_and_optional_observation() -> None:
    sensor_repo = _SensorRepo()
    event_repo = _EventRepo()
    result = await MMWaveIngestService().ingest_payload(
        "baby/radar/telemetry",
        b'{"device_id":"radar-1","timestamp":"2026-08-01T00:00:00Z",'
        b'"presence":true,"state":"moving","abnormal_event":"apnea_candidate"}',
        sensor_repo=sensor_repo,
        event_repo=event_repo,
        baby_id="baby-1",
        family_id="family-1",
    )

    assert result.sensor_event.signal_type == "apnea_candidate"
    assert result.observation_event is not None
    assert result.observation_event.event_type == "mmwave_telemetry"
    assert sensor_repo.records[0].device_id == "radar-1"
    assert event_repo.events[0].source == "sensor"


def test_mmwave_worker_config_and_snapshot_defaults() -> None:
    config = MMWaveMQTTWorkerConfig()
    snapshot = MMWaveMQTTWorkerSnapshot()

    assert config.topics == ["baby/radar/telemetry"]
    assert snapshot.started is False
    assert snapshot.received_count == 0
