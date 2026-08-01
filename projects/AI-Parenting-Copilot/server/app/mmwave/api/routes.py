# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 14:35:00

"""mmWave frame ingestion API."""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from server.app.events.infra.sqlalchemy_repository import SQLAlchemyEventRepository
from server.app.mmwave.frame_parser import parse_radar_frame
from server.app.mmwave.sensor_event_mapper import (
    map_frame_to_observation_event,
    map_frame_to_sensor_event,
)
from server.app.mmwave.sqlalchemy_sensor_event_repo import (
    SensorEventRecord,
    SQLAlchemySensorEventRepository,
)
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1/mmwave", tags=["mmwave"])


class MMWaveFrameIngestRequest(BaseModel):
    topic: str = "baby/radar/telemetry"
    frame: dict[str, object] = Field(default_factory=dict)
    baby_id: str | None = None
    family_id: str | None = None


class MMWaveFrameIngestResponse(BaseModel):
    sensor_event: SensorEventRecord
    observation_event_id: str | None = None


@router.post("/frames", response_model=MMWaveFrameIngestResponse)
async def ingest_mmwave_frame(
    payload: MMWaveFrameIngestRequest,
    request: Request,
) -> MMWaveFrameIngestResponse:
    frame = parse_radar_frame(json.dumps(payload.frame), topic=payload.topic)
    candidate = map_frame_to_sensor_event(frame)
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        sensor_event = await SQLAlchemySensorEventRepository(db_session).add(candidate)
    else:
        sensor_event = SensorEventRecord(
            device_id=candidate.device_id,
            ts=candidate.ts,
            signal_type=candidate.signal_type,
            payload=candidate.payload,
        )
    observation_event_id: str | None = None
    if db_session is not None and payload.baby_id and payload.family_id:
        observation = await SQLAlchemyEventRepository(db_session).upsert(
            map_frame_to_observation_event(
                frame,
                baby_id=payload.baby_id,
                family_id=payload.family_id,
            )
        )
        observation_event_id = observation.event_id
    await record_request_audit(
        request,
        action="mmwave.frame_ingest",
        resource=f"sensor_event:{sensor_event.id}",
        after={
            "sensor_event": sensor_event.model_dump(mode="json"),
            "observation_event_id": observation_event_id,
        },
        db_only=True,
    )
    return MMWaveFrameIngestResponse(
        sensor_event=sensor_event,
        observation_event_id=observation_event_id,
    )
