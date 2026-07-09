# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:05:00


"""ObservationEvent contract SSOT for sync/API/normalization."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid

JsonDict = dict[str, Any]


class EventSource(StrEnum):
    MANUAL = "manual"
    VOICE_TEXT = "voice_text"
    CAMERA = "camera"
    SENSOR = "sensor"
    AI = "ai"
    SYSTEM = "system"


class SyncStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    NORMALIZED = "normalized"
    PROJECTED = "projected"


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("datetime must be timezone-aware")
    return value


class ObservationEventCreate(BaseModel):
    """Input contract for a synchronized observation event."""

    model_config = ConfigDict(use_enum_values=True)

    event_id: str = Field(default_factory=new_ulid)
    baby_id: str
    family_id: str
    user_id: str | None = None
    device_id: str | None = None
    event_type: str = Field(min_length=1, max_length=64)
    start_time: datetime
    end_time: datetime | None = None
    client_created_at: datetime
    raw_input: JsonDict = Field(default_factory=dict)
    normalized_payload: JsonDict = Field(default_factory=dict)
    payload: JsonDict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: EventSource
    attachments: JsonDict = Field(default_factory=dict)
    correction_of: str | None = None
    is_deleted: bool = False

    @field_validator("start_time", "end_time", "client_created_at")
    @classmethod
    def datetime_must_be_aware(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _ensure_aware(value)


class ObservationEvent(ObservationEventCreate):
    """Persisted ObservationEvent with server lifecycle fields."""

    server_received_at: datetime = Field(default_factory=utc_now)
    sync_status: SyncStatus = SyncStatus.PENDING
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class EventCorrectionRequest(BaseModel):
    """Request to create a correction event for an existing event."""

    normalized_payload: JsonDict = Field(default_factory=dict)
    raw_input: JsonDict = Field(default_factory=dict)
    reason: str | None = None
    client_created_at: datetime = Field(default_factory=utc_now)

    @field_validator("client_created_at")
    @classmethod
    def correction_time_must_be_aware(cls, value: datetime) -> datetime:
        return _ensure_aware(value)
