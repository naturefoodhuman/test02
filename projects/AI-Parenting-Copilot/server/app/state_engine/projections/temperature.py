# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00

"""Temperature projection."""
from __future__ import annotations

from server.app.normalization.service import NormalizedRecord


def _float_value(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float | str | bytes | bytearray):
        return float(value)
    return None


def project_temperature(records: list[NormalizedRecord]) -> dict[str, object]:
    values = [
        value
        for value in (_float_value(record.payload.get("value_c")) for record in records)
        if value is not None
    ]
    return {"temperature_max_24h_c": max(values) if values else None}
