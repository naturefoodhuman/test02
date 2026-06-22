# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:18:00

"""
PIIReplacer — deterministic placeholder replacement (E5-C6-S1-T1).

Per NETWORK_ARCHITECTURE_FINAL.md §10.2 and TASK_BACKLOG E5-C6-S1-T1.

Responsibilities:
- Replace detected PIIEntity spans with stable placeholders.
- Reuse the same placeholder for the same raw value in one replacement run.
- Return a mapping_id and queryable mapping for the next persistence layer.

Important boundary:
- This task implements replacement + in-process mapping storage.
- SQLCipher-backed ``runtime/pii_map.db`` persistence is the next task
  (E5-C6-S1-T2). The store interface here is intentionally small so the
  encrypted DB implementation can plug in without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional
from uuid import uuid4

from .models import PIIEntity, PIIType


@dataclass(frozen=True)
class PIIPlaceholderMapping:
    """One placeholder ↔ original entity mapping entry."""

    placeholder: str
    type: PIIType
    value: str
    recognizer: str
    score: float


@dataclass(frozen=True)
class PIIReplacementResult:
    """Result of a placeholder replacement run."""

    text: str
    mapping_id: str
    mapping: Mapping[str, PIIPlaceholderMapping]
    entities: List[PIIEntity]

    @property
    def placeholders(self) -> list[str]:
        return list(self.mapping.keys())


class InMemoryPIIMapStore:
    """
    Minimal queryable mapping store used until SQLCipher DB arrives (T2).

    Stored data is process-local only. It is sufficient for T1 unit tests and
    provides the seam for the encrypted implementation in E5-C6-S1-T2.
    """

    def __init__(self):
        self._data: dict[str, Mapping[str, PIIPlaceholderMapping]] = {}

    def save(self, mapping_id: str, mapping: Mapping[str, PIIPlaceholderMapping]) -> None:
        self._data[mapping_id] = dict(mapping)

    def get(self, mapping_id: str) -> Mapping[str, PIIPlaceholderMapping]:
        return dict(self._data[mapping_id])

    def has(self, mapping_id: str) -> bool:
        return mapping_id in self._data


class PIIReplacer:
    """Replace PII spans with deterministic placeholders."""

    def __init__(
        self,
        placeholder_format: str = "PII_{entity_type}_{index:03d}",
        store: InMemoryPIIMapStore | None = None,
    ):
        self.placeholder_format = placeholder_format
        self.store = store or InMemoryPIIMapStore()

    @staticmethod
    def _select_non_overlapping_entities(entities: Iterable[PIIEntity]) -> list[PIIEntity]:
        """
        Select non-overlapping spans.

        Priority:
        1. lower start offset
        2. longer span for same start
        3. higher confidence score
        """
        sorted_entities = sorted(
            entities,
            key=lambda entity: (entity.start, -(entity.end - entity.start), -entity.score),
        )
        selected: list[PIIEntity] = []
        current_end = -1
        for entity in sorted_entities:
            if entity.end <= entity.start:
                continue
            if entity.start < current_end:
                continue
            selected.append(entity)
            current_end = entity.end
        return selected

    def _make_placeholder(self, entity_type: PIIType, index: int) -> str:
        return self.placeholder_format.format(
            entity_type=entity_type.value,
            type=entity_type.value,
            index=index,
        )

    def replace(
        self,
        text: str,
        entities: Iterable[PIIEntity],
        mapping_id: Optional[str] = None,
    ) -> PIIReplacementResult:
        """
        Replace PIIEntity spans in text and store a queryable placeholder map.

        The same raw value reuses the same placeholder within this replacement
        run, even if detected by multiple recognizers.
        """
        mapping_id = mapping_id or str(uuid4())
        selected = self._select_non_overlapping_entities(entities)
        if not text or not selected:
            self.store.save(mapping_id, {})
            return PIIReplacementResult(
                text=text,
                mapping_id=mapping_id,
                mapping={},
                entities=[],
            )

        value_to_placeholder: dict[str, str] = {}
        mapping: dict[str, PIIPlaceholderMapping] = {}
        next_index = 1

        pieces: list[str] = []
        cursor = 0
        for entity in selected:
            start = max(0, min(entity.start, len(text)))
            end = max(0, min(entity.end, len(text)))
            if start < cursor or end <= start:
                continue

            pieces.append(text[cursor:start])

            if entity.value in value_to_placeholder:
                placeholder = value_to_placeholder[entity.value]
            else:
                placeholder = self._make_placeholder(entity.type, next_index)
                next_index += 1
                value_to_placeholder[entity.value] = placeholder
                mapping[placeholder] = PIIPlaceholderMapping(
                    placeholder=placeholder,
                    type=entity.type,
                    value=entity.value,
                    recognizer=entity.recognizer,
                    score=entity.score,
                )

            pieces.append(placeholder)
            cursor = end

        pieces.append(text[cursor:])
        redacted_text = "".join(pieces)
        self.store.save(mapping_id, mapping)

        return PIIReplacementResult(
            text=redacted_text,
            mapping_id=mapping_id,
            mapping=mapping,
            entities=selected,
        )

    def get_mapping(self, mapping_id: str) -> Mapping[str, PIIPlaceholderMapping]:
        """Return a stored mapping by mapping_id."""
        return self.store.get(mapping_id)


__all__ = [
    "InMemoryPIIMapStore",
    "PIIPlaceholderMapping",
    "PIIReplacementResult",
    "PIIReplacer",
]
