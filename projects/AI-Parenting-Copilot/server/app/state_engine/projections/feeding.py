# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 22:20:00

"""Feeding projection with a true rolling 24h window."""

from __future__ import annotations

from datetime import datetime, timedelta

from server.app.common.clock import utc_now
from server.app.normalization.service import NormalizedRecord


def _float_value(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, int | float | str | bytes | bytearray):
        return float(value)
    return 0.0


def _record_time(record: NormalizedRecord) -> datetime:
    raw_value = (
        record.payload.get("fed_at") or record.payload.get("start_time") or record.created_at
    )
    parsed = datetime.fromisoformat(str(raw_value))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=utc_now().tzinfo)
    return parsed


def project_feeding(
    records: list[NormalizedRecord],
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Project feeding stats for records in the last 24 hours only."""

    reference_time = now or utc_now()
    window_start = reference_time - timedelta(hours=24)
    feeding = [
        record
        for record in records
        if record.record_type == "feeding" and _record_time(record) >= window_start
    ]
    total_ml = sum(_float_value(record.payload.get("amount_ml")) for record in feeding)
    last = max((_record_time(record).isoformat() for record in feeding), default=None)
    return {
        "feeding_24h_ml": total_ml,
        "feeding_24h_count": len(feeding),
        "last_feeding_at": last,
    }
