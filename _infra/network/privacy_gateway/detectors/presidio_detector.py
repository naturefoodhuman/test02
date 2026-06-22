"""
PresidioDetector — Microsoft Presidio based PII detector

Per TASK_BACKLOG E5-C3-S1-T2 / T3 + NETWORK_ENGINEERING_DESIGN §5.3

Supports custom Chinese recognizers via ad-hoc or registry.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

from presidio_analyzer import AnalyzerEngine, RecognizerResult

from .base import PIIDetector
from ..models import PIIEntity, PIIType

try:
    from ..recognizers.cn_recognizers import get_cn_recognizers
except ImportError:
    def get_cn_recognizers():
        return []

PRESIDIO_TO_PII_TYPE: Dict[str, PIIType] = {
    "EMAIL_ADDRESS": PIIType.EMAIL_ADDRESS,
    "PHONE_NUMBER": PIIType.PHONE_NUMBER,
    "CREDIT_CARD": PIIType.CREDIT_CARD,
    "IP_ADDRESS": PIIType.IP_ADDRESS,
    "PERSON": PIIType.PERSON,
    "LOCATION": PIIType.LOCATION,
    "ORGANIZATION": PIIType.ORGANIZATION,
    "CN_PHONE": PIIType.CN_PHONE,
    "CN_ID_CARD": PIIType.CN_ID_CARD,
    "BANK_CARD": PIIType.BANK_CARD,
    "CN_ADDRESS": PIIType.CN_ADDRESS,
}


class PresidioDetector(PIIDetector):
    def __init__(
        self,
        language: str = "en",
        timeout: float = 5.0,
        additional_recognizers: Optional[List] = None,
        load_cn_recognizers: bool = True,
    ):
        self._language = language
        self._timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._analyzer: AnalyzerEngine | None = None
        self._additional_recognizers: List = list(additional_recognizers or [])

        if load_cn_recognizers and language in ("zh", "zh-cn"):
            self._additional_recognizers.extend(get_cn_recognizers())

    def _get_analyzer(self) -> AnalyzerEngine:
        if self._analyzer is None:
            self._analyzer = AnalyzerEngine()
            for rec in self._additional_recognizers:
                try:
                    self._analyzer.registry.add_recognizer(rec)
                except Exception:
                    pass
        return self._analyzer

    async def detect(self, text: str) -> List[PIIEntity]:
        if not text or not text.strip():
            return []

        analyzer = self._get_analyzer()

        def _analyze() -> List[RecognizerResult]:
            # Use ad_hoc for custom recognizers to ensure they run
            ad_hoc = self._additional_recognizers if self._additional_recognizers else None
            return analyzer.analyze(
                text=text,
                language=self._language,
                ad_hoc_recognizers=ad_hoc,
            )

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
                continue
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

        entities.sort(key=lambda e: e.start)
        return entities

    def get_name(self) -> str:
        return "presidio"

    async def health_check(self) -> bool:
        try:
            results = await self.detect("My email is test@example.com")
            return len(results) > 0
        except Exception:
            return False

    def supports_type(self, pii_type: PIIType) -> bool:
        return pii_type in PRESIDIO_TO_PII_TYPE.values()

    def register_recognizer(self, recognizer) -> None:
        self._additional_recognizers.append(recognizer)
        if self._analyzer is not None:
            try:
                self._analyzer.registry.add_recognizer(recognizer)
            except Exception:
                pass
