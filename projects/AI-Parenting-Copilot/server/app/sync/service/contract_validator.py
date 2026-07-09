# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00


"""PowerSync write contract validator and soft conflict hints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from server.app.common.errors import AppError

REQUIRED_SYNC_FIELDS = {
    "event_id",
    "baby_id",
    "family_id",
    "user_id",
    "device_id",
    "event_type",
    "client_created_at",
    "payload",
    "source",
    "confidence",
    "is_deleted",
    "correction_of",
}


class SyncContractError(AppError):
    status_code = 422
    code = "SYNC_CONTRACT_INVALID"


class ConflictHint(BaseModel):
    kind: str
    message: str
    event_ids: list[str] = Field(default_factory=list)


def validate_sync_record(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_SYNC_FIELDS - set(record))
    if missing:
        raise SyncContractError(
            "Sync record is missing required fields",
            evidence={"missing": missing},
        )
    if record.get("source") not in {"manual", "voice_text", "camera", "sensor", "ai", "system"}:
        raise SyncContractError("Invalid sync source", evidence={"source": record.get("source")})
    raw_confidence = record.get("confidence")
    if not isinstance(raw_confidence, int | float | str | bytes | bytearray):
        raise SyncContractError("confidence is required")
    confidence = float(raw_confidence)
    if confidence < 0 or confidence > 1:
        raise SyncContractError("confidence must be between 0 and 1")


def feeding_duplicate_hint(records: list[dict[str, Any]]) -> ConflictHint | None:
    feeding = [record for record in records if record.get("event_type") == "feeding"]
    feeding.sort(key=lambda record: str(record.get("client_created_at")))
    for prev, cur in zip(feeding, feeding[1:], strict=False):
        prev_time = datetime.fromisoformat(str(prev["client_created_at"]))
        cur_time = datetime.fromisoformat(str(cur["client_created_at"]))
        if abs((cur_time - prev_time).total_seconds()) <= 5 * 60:
            return ConflictHint(
                kind="duplicate_feeding_soft_hint",
                message="5分钟内存在疑似重复喂奶记录，请人工确认；系统不自动删除。",
                event_ids=[str(prev["event_id"]), str(cur["event_id"])],
            )
    return None
