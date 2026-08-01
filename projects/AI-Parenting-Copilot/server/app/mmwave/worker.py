# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 18:12:00

"""MQTT worker for mmWave radar telemetry ingestion."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import aiomqtt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from server.app.events.infra.sqlalchemy_repository import SQLAlchemyEventRepository
from server.app.mmwave.ingest_service import MMWaveIngestResult, MMWaveIngestService
from server.app.mmwave.sqlalchemy_sensor_event_repo import SQLAlchemySensorEventRepository


@dataclass(slots=True)
class MMWaveMQTTWorkerConfig:
    host: str = "127.0.0.1"
    port: int = 1883
    topics: list[str] = field(default_factory=lambda: ["baby/radar/telemetry"])
    baby_id: str | None = None
    family_id: str | None = None
    reconnect_backoff_seconds: float = 1.0


@dataclass(slots=True)
class MMWaveMQTTWorkerSnapshot:
    started: bool = False
    received_count: int = 0
    persisted_sensor_count: int = 0
    persisted_observation_count: int = 0
    last_error: str | None = None
    last_signal_type: str | None = None


class MMWaveMQTTWorker:
    """At-least-once MQTT consumer; DB writes are idempotent at upper event layer."""

    name = "mmwave-mqtt-worker"

    def __init__(
        self,
        *,
        config: MMWaveMQTTWorkerConfig,
        session_factory: async_sessionmaker[AsyncSession],
        ingest_service: MMWaveIngestService | None = None,
    ) -> None:
        self.config = config
        self.session_factory = session_factory
        self.ingest_service = ingest_service or MMWaveIngestService()
        self.snapshot = MMWaveMQTTWorkerSnapshot()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self.snapshot.started = True
        self._task = asyncio.create_task(self._run_forever())

    async def stop(self) -> None:
        self.snapshot.started = False
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def process_message(self, topic: str, payload: str | bytes) -> MMWaveIngestResult:
        async with self.session_factory() as session:
            async with session.begin():
                result = await self.ingest_service.ingest_payload(
                    topic,
                    payload,
                    sensor_repo=SQLAlchemySensorEventRepository(session),
                    event_repo=SQLAlchemyEventRepository(session)
                    if self.config.baby_id and self.config.family_id
                    else None,
                    baby_id=self.config.baby_id,
                    family_id=self.config.family_id,
                )
        self.snapshot.received_count += 1
        self.snapshot.persisted_sensor_count += 1
        self.snapshot.last_signal_type = result.sensor_event.signal_type
        if result.observation_event is not None:
            self.snapshot.persisted_observation_count += 1
        self.snapshot.last_error = None
        return result

    async def _run_forever(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - requires live MQTT failures
                self.snapshot.last_error = str(exc)
                await asyncio.sleep(self.config.reconnect_backoff_seconds)

    async def _run_once(self) -> None:
        async with aiomqtt.Client(hostname=self.config.host, port=self.config.port) as client:
            for topic in self.config.topics:
                await client.subscribe(topic)
            async for message in client.messages:
                if self._stop_event.is_set():
                    return
                await self.process_message(str(message.topic), _payload_bytes(message.payload))


def _payload_bytes(payload: Any) -> bytes | str:
    if isinstance(payload, bytes | str):
        return payload
    return bytes(payload)
