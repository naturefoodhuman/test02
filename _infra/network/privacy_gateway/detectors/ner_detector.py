# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:54:33

"""
SpaCyNERDetector — spaCy based NER detector (E5-C4-S1-T1).

Per NETWORK_ARCHITECTURE_FINAL.md §10.5 and TASK_BACKLOG E5-C4-S1-T1.

This detector is part of Privacy Gateway L3. It maps spaCy entity labels to the
canonical PIIEntity model:
- PERSON / PER -> PIIType.PERSON
- ORG -> PIIType.ORGANIZATION
- GPE / LOC / FAC -> PIIType.LOCATION

Importing this module is safe when spaCy models are not installed. The detector
supports dependency injection for unit tests and returns no detections when no
model can be loaded.
"""

from __future__ import annotations

import re
from typing import Any, List, Optional

from .base import PIIDetector
from ..models import PIIEntity, PIIType

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

SPACY_LABEL_TO_PII_TYPE: dict[str, PIIType] = {
    "PERSON": PIIType.PERSON,
    "PER": PIIType.PERSON,
    "ORG": PIIType.ORGANIZATION,
    "GPE": PIIType.LOCATION,
    "LOC": PIIType.LOCATION,
    "FAC": PIIType.LOCATION,
}


class SpaCyNERDetector(PIIDetector):
    """
    spaCy-backed NER detector for person / organization / location entities.

    The detector loads both Chinese and English models by default when
    available. Tests can inject lightweight fake ``zh_nlp`` / ``en_nlp`` objects
    with spaCy-compatible ``doc.ents`` output.
    """

    def __init__(
        self,
        zh_model: str = "zh_core_web_sm",
        en_model: str = "en_core_web_sm",
        zh_nlp: Any | None = None,
        en_nlp: Any | None = None,
        load_models: bool = True,
        score: float = 0.85,
    ):
        self.zh_model = zh_model
        self.en_model = en_model
        self._zh_nlp = zh_nlp
        self._en_nlp = en_nlp
        self._score = score

        if load_models:
            if self._zh_nlp is None:
                self._zh_nlp = self._load_spacy_model(zh_model)
            if self._en_nlp is None:
                self._en_nlp = self._load_spacy_model(en_model)

    @staticmethod
    def _load_spacy_model(model_name: str) -> Any | None:
        try:
            import spacy

            return spacy.load(model_name)
        except Exception:
            return None

    @staticmethod
    def _looks_chinese(text: str) -> bool:
        return bool(_CJK_RE.search(text))

    def _select_nlp(self, text: str) -> Any | None:
        """Prefer Chinese model for CJK text, English model otherwise."""
        if self._looks_chinese(text):
            return self._zh_nlp or self._en_nlp
        return self._en_nlp or self._zh_nlp

    async def detect(self, text: str) -> List[PIIEntity]:
        if not text or not text.strip():
            return []

        nlp = self._select_nlp(text)
        if nlp is None:
            return []

        doc = nlp(text)
        entities: list[PIIEntity] = []
        for ent in getattr(doc, "ents", []):
            label = str(getattr(ent, "label_", ""))
            pii_type = SPACY_LABEL_TO_PII_TYPE.get(label)
            if pii_type is None:
                continue

            start = int(getattr(ent, "start_char"))
            end = int(getattr(ent, "end_char"))
            value = text[start:end]
            if not value:
                continue

            entities.append(
                PIIEntity(
                    type=pii_type,
                    value=value,
                    start=start,
                    end=end,
                    score=self._score,
                    recognizer=f"spacy:{label}",
                )
            )

        entities.sort(key=lambda entity: entity.start)
        return entities

    def get_name(self) -> str:
        return "spacy_ner"

    async def health_check(self) -> bool:
        return self._zh_nlp is not None or self._en_nlp is not None

    def supports_type(self, pii_type: PIIType) -> bool:
        return pii_type in {
            PIIType.PERSON,
            PIIType.ORGANIZATION,
            PIIType.LOCATION,
        }


__all__ = ["SPACY_LABEL_TO_PII_TYPE", "SpaCyNERDetector"]
