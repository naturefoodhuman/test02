# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Manual/form parser for P0 record types."""

from __future__ import annotations

from server.app.events.domain.observation_event import ObservationEvent


def parse_form_event(event: ObservationEvent) -> tuple[str, dict[str, object], float]:
    payload = dict(event.payload or event.normalized_payload or {})
    if event.event_type in {"feeding", "diaper", "sleep", "temperature", "supplement"}:
        return event.event_type, payload, 1.0 if event.source == "manual" else event.confidence
    return "unknown", payload, event.confidence
