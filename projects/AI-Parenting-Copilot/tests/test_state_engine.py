# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""APC-T015/T016 state engine tests."""

from __future__ import annotations

from server.app.normalization.service import NormalizedRecord
from server.app.state_engine.engine import BabyStateEngine


def test_state_engine_projection_is_order_independent() -> None:
    records = [
        NormalizedRecord(
            event_id="e1",
            baby_id="baby-1",
            family_id="family-1",
            record_type="feeding",
            payload={"amount_ml": 90},
            confidence=1.0,
        ),
        NormalizedRecord(
            event_id="e2",
            baby_id="baby-1",
            family_id="family-1",
            record_type="temperature",
            payload={"value_c": 37.8},
            confidence=1.0,
        ),
        NormalizedRecord(
            event_id="e3",
            baby_id="baby-1",
            family_id="family-1",
            record_type="diaper",
            payload={"note": "湿尿布"},
            confidence=1.0,
        ),
    ]

    first = BabyStateEngine().recompute(baby_id="baby-1", family_id="family-1", records=records)
    second = BabyStateEngine().recompute(
        baby_id="baby-1",
        family_id="family-1",
        records=list(reversed(records)),
    )

    assert first.snapshot["feeding_24h_ml"] == 90
    assert first.snapshot["temperature_max_24h_c"] == 37.8
    assert first.snapshot["diaper_wet_24h"] == 1
    assert first.snapshot["feeding_24h_ml"] == second.snapshot["feeding_24h_ml"]


def test_feeding_projection_uses_rolling_24h_window() -> None:
    from datetime import UTC, datetime, timedelta

    from server.app.state_engine.projections.feeding import project_feeding

    now = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
    recent = NormalizedRecord(
        event_id="recent",
        baby_id="baby-1",
        family_id="family-1",
        record_type="feeding",
        payload={"amount_ml": 90, "fed_at": (now - timedelta(hours=2)).isoformat()},
        confidence=1.0,
    )
    old = NormalizedRecord(
        event_id="old",
        baby_id="baby-1",
        family_id="family-1",
        record_type="feeding",
        payload={"amount_ml": 120, "fed_at": (now - timedelta(hours=25)).isoformat()},
        confidence=1.0,
    )

    projection = project_feeding([recent, old], now=now)

    assert projection["feeding_24h_ml"] == 90
    assert projection["feeding_24h_count"] == 1
    assert projection["last_feeding_at"] == recent.payload["fed_at"]
