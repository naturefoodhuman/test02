"""
PresidioDetector — Microsoft Presidio based PII detector

Per TASK_BACKLOG E5-C3-S1-T2 + NETWORK_ENGINEERING_DESIGN §5.3
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

from presidio_analyzer import AnalyzerEngine, RecognizerResult

from .base import PIIDetector
from ..models import PIIEntity, PIIType


# Mapping from Presidio entity types to our PIIType
PRESIDIO_TO_PII_TYPE: Dict[str, PIIType] = {
    "EMAIL_ADDRESS": PIIType.EMAIL_ADDRESS,
    "PHONE_NUMBER": PIIType.PHONE_NUMBER,
    "CREDIT_CARD": PIIType.CREDIT_CARD,
    "IP_ADDRESS": PIIType.IP_ADDRESS,
    "PERSON": PIIType.PERSON,
    "LOCATION": PIIType.LOCATION,
    "ORGANIZATION": PIIType.ORGANIZATION,
    # Add more as needed
}


class PresidioDetector(PIIDetector):
    """
    PII detector powered by Microsoft Presidio AnalyzerEngine.

    - Runs synchronously inside a thread pool to keep the API async-friendly.
    - Default language: 'en'
    - Supports Chinese via language='zh' (requires appropriate recognizers)
    """

    def __init__(self, language: str = "en", timeout: float = 5.0):
        self._language = language
        self._timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._analyzer: AnalyzerEngine | None = None

    def _get_analyzer(self) -> AnalyzerEngine:
        if self._analyzer is None:
            self._analyzer = AnalyzerEngine()
        return self._analyzer

    async def detect(self, text: str) -> List[PIIEntity]:
        if not text or not text.strip():
            return []

        analyzer = self._get_analyzer()

        def _analyze() -> List[RecognizerResult]:
            return analyzer.analyze(text=text, language=self._language)

        loop = asyncio.get_running_loop()
        try:
            results: List[RecognizerResult] = await asyncio.wait_for(
                loop.run_in_executor(self._executor, _analyze),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            return []

        entities: List[PIIEntity] = []
        for res in results:
            pii_type = PRESIDIO_TO_PII_TYPE.get(res.entity_type)
            if not pii_type:
                continue  # skip unsupported types for now

            value = text[res.start : res.end]
            entities.append(
                PIIEntity(
                    type=pii_type,
                    value=value,
                    start=res.start,
                    end=res.end,
                    score=float(res.score),
                    recognizer=f"presidio:{res.entity_type}",
                )
            )

        # Sort by start offset (good practice)
        entities.sort(key=lambda e: e.start)
        return entities

    def get_name(self) -> str:
        return "presidio"

    async def health_check(self) -> bool:
        try:
            test_text = "My email is test@example.com"
            results = await self.detect(test_text)
            return len(results) > 0
        except Exception:
            return False

    def supports_type(self, pii_type: PIIType) -> bool:
        return pii_type in PRESIDIO_TO_PII_TYPE.values()
