# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 04:25:00


"""M1-M5 memory snapshot builder.

This is a structured-first in-memory implementation used by Orchestrator tests while
PostgreSQL/Local RAG backed stores are waiting for integration validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

JsonDict = dict[str, Any]


@dataclass(slots=True)
class MemorySnapshot:
    baby_id: str | None = None
    family_id: str | None = None
    hard_facts: JsonDict = field(default_factory=dict)
    family_preferences: JsonDict = field(default_factory=dict)
    behavior_baseline: JsonDict = field(default_factory=dict)
    short_context: JsonDict = field(default_factory=dict)
    correction_memory: JsonDict = field(default_factory=dict)
    rule_versions: JsonDict = field(default_factory=dict)

    def to_context(self) -> JsonDict:
        return {
            "baby_id": self.baby_id,
            "family_id": self.family_id,
            "hard_facts": self.hard_facts,
            "family_preferences": self.family_preferences,
            "behavior_baseline": self.behavior_baseline,
            "short_context": self.short_context,
            "correction_memory": self.correction_memory,
            "rule_versions": self.rule_versions,
        }


class MemoryStore:
    """In-memory M1-M5 store used until DB/RAG backed implementation lands."""

    def __init__(self) -> None:
        self._facts: dict[str, JsonDict] = {}
        self._preferences: dict[str, JsonDict] = {}
        self._baseline: dict[str, JsonDict] = {}
        self._short_context: dict[str, JsonDict] = {}
        self._corrections: dict[str, JsonDict] = {}

    def set_baby_facts(self, baby_id: str, facts: JsonDict) -> None:
        self._facts[baby_id] = dict(facts)

    def set_family_preferences(self, family_id: str, preferences: JsonDict) -> None:
        self._preferences[family_id] = dict(preferences)

    def set_short_context(self, baby_id: str, context: JsonDict) -> None:
        self._short_context[baby_id] = dict(context)

    def set_corrections(self, family_id: str, corrections: JsonDict) -> None:
        self._corrections[family_id] = dict(corrections)

    def build_snapshot(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        rule_versions: JsonDict | None = None,
    ) -> MemorySnapshot:
        return MemorySnapshot(
            baby_id=baby_id,
            family_id=family_id,
            hard_facts=dict(self._facts.get(baby_id or "", {})),
            family_preferences=dict(self._preferences.get(family_id or "", {})),
            behavior_baseline=dict(self._baseline.get(baby_id or "", {})),
            short_context=dict(self._short_context.get(baby_id or "", {})),
            correction_memory=dict(self._corrections.get(family_id or "", {})),
            rule_versions=dict(rule_versions or {}),
        )
