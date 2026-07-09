# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00

"""Feeding projection."""

from __future__ import annotations

from server.app.normalization.service import NormalizedRecord


def _float_value(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, int | float | str | bytes | bytearray):
        return float(value)
    return 0.0


def project_feeding(records: list[NormalizedRecord]) -> dict[str, object]:
    feeding = [record for record in records if record.record_type == "feeding"]
    total_ml = sum(_float_value(record.payload.get("amount_ml")) for record in feeding)
    last = max((record.created_at for record in feeding), default=None)
    return {
        "feeding_24h_ml": total_ml,
        "feeding_24h_count": len(feeding),
        "last_feeding_at": last,
    }
