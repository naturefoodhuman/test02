# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Lightweight event bus contracts.

APC-T011 replaces this in-memory publisher with PG LISTEN/NOTIFY integration.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid


@dataclass(frozen=True)
class DomainEvent:
    """Internal domain event envelope."""

    name: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=new_ulid)
    occurred_at_iso: str = field(default_factory=lambda: utc_now().isoformat())


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventPublisher(Protocol):
    """Protocol for future PG-backed event publishers."""

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event."""


class InMemoryEventBus:
    """Test/dev event bus with explicit handler registration."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Subscribe a handler to a named event."""

        self._handlers.setdefault(event_name, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to current in-memory handlers."""

        for handler in self._handlers.get(event.name, []):
            await handler(event)


@dataclass(frozen=True)
class PgNotifyPayload:
    """Payload emitted by PostgreSQL NOTIFY `events.changed`."""

    event_id: str
    baby_id: str
    operation: str

    def to_dict(self) -> dict[str, str]:
        return {"event_id": self.event_id, "baby_id": self.baby_id, "operation": self.operation}


def parse_pg_notify_payload(payload: str) -> PgNotifyPayload:
    """Parse JSON NOTIFY payload from the DB trigger."""

    import json

    raw = json.loads(payload)
    return PgNotifyPayload(
        event_id=str(raw["event_id"]),
        baby_id=str(raw["baby_id"]),
        operation=str(raw["operation"]),
    )


def domain_event_from_pg_notify(payload: PgNotifyPayload) -> DomainEvent:
    return DomainEvent(name="events.changed", payload=payload.to_dict())
