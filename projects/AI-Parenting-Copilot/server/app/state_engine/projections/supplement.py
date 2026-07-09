# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Supplement projection."""

from __future__ import annotations

from server.app.normalization.service import NormalizedRecord


def project_supplement(records: list[NormalizedRecord]) -> dict[str, object]:
    todos = [
        r.payload
        for r in records
        if r.record_type == "supplement" and r.payload.get("status") == "todo"
    ]
    return {"supplement_todos": todos}
