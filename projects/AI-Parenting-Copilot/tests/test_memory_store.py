# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""APC-T026 memory snapshot tests."""

from __future__ import annotations

from server.app.memory import MemoryStore


def test_memory_store_builds_m1_to_m5_snapshot() -> None:
    store = MemoryStore()
    store.set_baby_facts("baby-1", {"age_days": 30, "weight_kg": 4.2})
    store.set_family_preferences("family-1", {"language": "zh-CN"})
    store.set_short_context("baby-1", {"last_feeding_minutes": 90})
    store.set_corrections("family-1", {"milk_unit": "ml"})

    snapshot = store.build_snapshot(
        baby_id="baby-1",
        family_id="family-1",
        rule_versions={"medication": "dev"},
    )

    assert snapshot.hard_facts["age_days"] == 30
    assert snapshot.family_preferences["language"] == "zh-CN"
    assert snapshot.short_context["last_feeding_minutes"] == 90
    assert snapshot.correction_memory["milk_unit"] == "ml"
    assert snapshot.rule_versions["medication"] == "dev"
