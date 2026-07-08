# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:05:00


"""Idempotency helpers for ObservationEvent writes."""

from __future__ import annotations

from server.app.common.errors import ConflictError
from server.app.events.domain.observation_event import ObservationEvent, ObservationEventCreate


def ensure_idempotent(existing: ObservationEvent | None, incoming: ObservationEventCreate) -> None:
    """Validate duplicate event_id semantics.

    A repeated event_id for the same baby/family/event_type is idempotent. A repeated
    event_id pointing at a different family, baby or type is treated as a conflict.
    """

    if existing is None:
        return
    if (
        existing.family_id != incoming.family_id
        or existing.baby_id != incoming.baby_id
        or existing.event_type != incoming.event_type
    ):
        raise ConflictError(
            "event_id already exists for a different event identity",
            evidence={"event_id": incoming.event_id},
        )
