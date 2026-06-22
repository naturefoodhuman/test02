"""
Unit tests for PIIDetector ABC + supporting models (E5-C3-S1-T1)
"""

from typing import List

import pytest

from _infra.network.privacy_gateway.models import PIIType, PIIEntity
from _infra.network.privacy_gateway.detectors.base import PIIDetector


def test_pii_type_enum_values():
    assert PIIType.EMAIL_ADDRESS.value == "EMAIL_ADDRESS"
    assert PIIType.CN_PHONE.value == "CN_PHONE"
    assert PIIType.API_KEY.value == "API_KEY"
    assert PIIType.PERSON.value == "PERSON"


def test_pii_type_is_str_enum():
    assert PIIType.PHONE_NUMBER == "PHONE_NUMBER"
    assert PIIType.CN_ID_CARD.value == "CN_ID_CARD"
    assert PIIType.CN_ID_CARD == "CN_ID_CARD"


def test_pii_entity_basic():
    entity = PIIEntity(
        type=PIIType.EMAIL_ADDRESS,
        value="alice@example.com",
        start=10,
        end=27,
        score=0.97,
        recognizer="presidio",
    )
    assert entity.type == PIIType.EMAIL_ADDRESS
    assert entity.length == 17
    assert entity.recognizer == "presidio"


def test_pii_entity_mask_full():
    entity = PIIEntity(type=PIIType.CREDIT_CARD, value="4111111111111111", start=0, end=16)
    assert entity.mask() == "41************11"


def test_pii_entity_mask_short():
    entity = PIIEntity(type=PIIType.CN_PHONE, value="1381234", start=0, end=7)
    assert entity.mask() == "13***34"


def test_pii_entity_mask_very_short():
    entity = PIIEntity(type=PIIType.PERSON, value="李", start=0, end=1)
    assert entity.mask() == "*"


def test_pii_entity_validation():
    with pytest.raises(Exception):
        PIIEntity(type=PIIType.EMAIL_ADDRESS, value="x", start=5)
    with pytest.raises(Exception):
        PIIEntity(type=PIIType.EMAIL_ADDRESS, value="x@x.com", start=-1, end=7)
    with pytest.raises(Exception):
        PIIEntity(type=PIIType.EMAIL_ADDRESS, value="x@x.com", start=0, end=7, score=1.5)


def test_pii_entity_extra_fields_forbidden():
    with pytest.raises(Exception):
        PIIEntity(type=PIIType.EMAIL_ADDRESS, value="x@x.com", start=0, end=7, foo="bar")


def test_piidetector_is_abstract():
    with pytest.raises(TypeError):
        PIIDetector()  # type: ignore


def test_piidetector_abstract_detect():
    class BadDetector(PIIDetector):
        pass
    with pytest.raises(TypeError):
        BadDetector()  # type: ignore


class DummyDetector(PIIDetector):
    async def detect(self, text: str) -> List[PIIEntity]:
        if "email" in text.lower():
            return [PIIEntity(type=PIIType.EMAIL_ADDRESS, value="test@example.com", start=0, end=16, recognizer="dummy")]
        return []

    def get_name(self) -> str:
        return "dummy"

    async def health_check(self) -> bool:
        return True


def test_dummy_detector_instantiation():
    det = DummyDetector()
    assert isinstance(det, PIIDetector)
    assert det.get_name() == "dummy"


def test_dummy_detector_detect():
    import asyncio
    det = DummyDetector()
    entities = asyncio.run(det.detect("Contact me at test@example.com"))
    assert len(entities) == 1
    assert entities[0].type == PIIType.EMAIL_ADDRESS
    assert entities[0].recognizer == "dummy"


def test_dummy_detector_empty():
    import asyncio
    det = DummyDetector()
    entities = asyncio.run(det.detect("No PII here"))
    assert entities == []


def test_dummy_health_check():
    import asyncio
    det = DummyDetector()
    assert asyncio.run(det.health_check()) is True


def test_supports_type_default():
    det = DummyDetector()
    assert det.supports_type(PIIType.EMAIL_ADDRESS) is True


def test_piientity_with_detector_name():
    entity = PIIEntity(type=PIIType.PERSON, value="张三", start=5, end=7, score=0.91, recognizer="dummy_cn")
    assert entity.recognizer == "dummy_cn"
    assert entity.mask() == "**"
