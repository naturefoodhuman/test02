# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00

"""APC-T011 PG notify payload tests."""

from __future__ import annotations

from pathlib import Path

from server.app.common.event_bus import domain_event_from_pg_notify, parse_pg_notify_payload


def test_pg_notify_payload_parse_and_domain_event() -> None:
    payload = parse_pg_notify_payload('{"event_id":"e1","baby_id":"b1","operation":"INSERT"}')
    event = domain_event_from_pg_notify(payload)

    assert payload.event_id == "e1"
    assert payload.baby_id == "b1"
    assert payload.operation == "INSERT"
    assert event.name == "events.changed"
    assert event.payload == {"event_id": "e1", "baby_id": "b1", "operation": "INSERT"}


def test_notify_trigger_migration_contains_required_channel_and_fields() -> None:
    migration = Path("server/migrations/versions/0002_event_notify_trigger.py").read_text()

    assert "events.changed" in migration
    assert "event_id" in migration
    assert "baby_id" in migration
    assert "TG_OP" in migration
