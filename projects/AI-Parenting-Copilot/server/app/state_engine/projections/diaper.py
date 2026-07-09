# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Diaper projection."""

from __future__ import annotations

from server.app.normalization.service import NormalizedRecord


def project_diaper(records: list[NormalizedRecord]) -> dict[str, object]:
    diapers = [r for r in records if r.record_type == "diaper"]
    dirty = [r for r in diapers if "便" in str(r.payload.get("note", ""))]
    return {"diaper_wet_24h": len(diapers), "diaper_dirty_24h": len(dirty)}
