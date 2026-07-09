# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Normalization dedup and correction helpers."""

from __future__ import annotations

from datetime import datetime

from server.app.normalization.service import NormalizedRecord


def is_duplicate_feeding(first: NormalizedRecord, second: NormalizedRecord) -> bool:
    if first.record_type != "feeding" or second.record_type != "feeding":
        return False
    first_time = first.payload.get("fed_at") or first.created_at
    second_time = second.payload.get("fed_at") or second.created_at
    delta = abs(datetime.fromisoformat(str(first_time)) - datetime.fromisoformat(str(second_time)))
    return delta.total_seconds() <= 5 * 60


def apply_correction(records: list[NormalizedRecord]) -> list[NormalizedRecord]:
    corrected_event_ids = {record.correction_of for record in records if record.correction_of}
    return [
        record
        for record in records
        if record.event_id not in corrected_event_ids and not record.is_deleted
    ]
