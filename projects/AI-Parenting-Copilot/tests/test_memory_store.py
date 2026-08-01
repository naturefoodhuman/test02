# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 23:20:00


"""APC-T026 memory snapshot tests."""

from __future__ import annotations

from dataclasses import dataclass

from server.app.memory import MemoryStore
from server.app.memory.local_rag import LocalRAGMemoryAdapter


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


@dataclass(frozen=True)
class _FakeChunk:
    content: str


@dataclass(frozen=True)
class _FakeDocument:
    source_url: str
    title: str


@dataclass(frozen=True)
class _FakeRetrieved:
    chunk: _FakeChunk
    document: _FakeDocument
    score: float


class _FakeRAGStore:
    def search(self, query: str, top_k: int = 5) -> list[_FakeRetrieved]:
        return [
            _FakeRetrieved(
                chunk=_FakeChunk(content=f"correction for {query}"),
                document=_FakeDocument(
                    source_url="local://family-corrections",
                    title="Family Corrections",
                ),
                score=0.9,
            )
        ][:top_k]


def test_local_rag_memory_adapter_normalizes_factory_results() -> None:
    adapter = LocalRAGMemoryAdapter(_FakeRAGStore())

    results = adapter.search_corrections("milk unit", limit=1)

    assert adapter.available() is True
    assert results == [
        {
            "content": "correction for milk unit",
            "score": 0.9,
            "source_url": "local://family-corrections",
            "title": "Family Corrections",
        }
    ]
