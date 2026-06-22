# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:54:33

"""
Unit tests for SpaCyNERDetector (E5-C4-S1-T1).

Tests use injected fake spaCy-compatible NLP objects so they do not require
actual zh_core_web_sm / en_core_web_sm model downloads.
"""

import asyncio
from dataclasses import dataclass

from _infra.network.privacy_gateway.detectors import SpaCyNERDetector
from _infra.network.privacy_gateway.detectors.ner_detector import SPACY_LABEL_TO_PII_TYPE
from _infra.network.privacy_gateway.models import PIIType


@dataclass
class FakeEnt:
    text: str
    label_: str
    start_char: int
    end_char: int


class FakeDoc:
    def __init__(self, ents):
        self.ents = ents


class FakeNLP:
    def __init__(self, entity_map: dict[str, str]):
        self.entity_map = entity_map
        self.calls: list[str] = []

    def __call__(self, text: str) -> FakeDoc:
        self.calls.append(text)
        ents = []
        for value, label in self.entity_map.items():
            start = text.find(value)
            if start >= 0:
                ents.append(FakeEnt(value, label, start, start + len(value)))
        return FakeDoc(ents)


def test_spacy_label_mapping():
    assert SPACY_LABEL_TO_PII_TYPE["PERSON"] == PIIType.PERSON
    assert SPACY_LABEL_TO_PII_TYPE["PER"] == PIIType.PERSON
    assert SPACY_LABEL_TO_PII_TYPE["ORG"] == PIIType.ORGANIZATION
    assert SPACY_LABEL_TO_PII_TYPE["GPE"] == PIIType.LOCATION
    assert SPACY_LABEL_TO_PII_TYPE["LOC"] == PIIType.LOCATION


def test_spacy_ner_detects_chinese_person_and_location():
    zh = FakeNLP({"张三": "PERSON", "北京市": "GPE"})
    en = FakeNLP({"Alice": "PERSON"})
    detector = SpaCyNERDetector(zh_nlp=zh, en_nlp=en, load_models=False)

    text = "张三住在北京市朝阳区。"
    entities = asyncio.run(detector.detect(text))

    assert [entity.value for entity in entities] == ["张三", "北京市"]
    assert [entity.type for entity in entities] == [PIIType.PERSON, PIIType.LOCATION]
    assert all(entity.recognizer.startswith("spacy:") for entity in entities)
    assert zh.calls == [text]
    assert en.calls == []


def test_spacy_ner_detects_english_person_org_location():
    en = FakeNLP({"Alice": "PERSON", "OpenAI": "ORG", "San Francisco": "GPE"})
    detector = SpaCyNERDetector(en_nlp=en, load_models=False)

    text = "Alice works at OpenAI in San Francisco."
    entities = asyncio.run(detector.detect(text))

    assert [entity.value for entity in entities] == ["Alice", "OpenAI", "San Francisco"]
    assert [entity.type for entity in entities] == [
        PIIType.PERSON,
        PIIType.ORGANIZATION,
        PIIType.LOCATION,
    ]


def test_spacy_ner_ignores_unsupported_labels():
    en = FakeNLP({"Monday": "DATE", "Alice": "PERSON"})
    detector = SpaCyNERDetector(en_nlp=en, load_models=False)

    entities = asyncio.run(detector.detect("Alice called on Monday."))

    assert [entity.value for entity in entities] == ["Alice"]
    assert entities[0].type == PIIType.PERSON


def test_spacy_ner_no_models_returns_empty():
    detector = SpaCyNERDetector(load_models=False)
    assert asyncio.run(detector.detect("Alice works at OpenAI.")) == []
    assert asyncio.run(detector.health_check()) is False


def test_spacy_ner_health_and_supports_type():
    detector = SpaCyNERDetector(en_nlp=FakeNLP({}), load_models=False)

    assert asyncio.run(detector.health_check()) is True
    assert detector.get_name() == "spacy_ner"
    assert detector.supports_type(PIIType.PERSON) is True
    assert detector.supports_type(PIIType.ORGANIZATION) is True
    assert detector.supports_type(PIIType.LOCATION) is True
    assert detector.supports_type(PIIType.EMAIL_ADDRESS) is False


def test_spacy_ner_empty_text():
    detector = SpaCyNERDetector(en_nlp=FakeNLP({"Alice": "PERSON"}), load_models=False)
    assert asyncio.run(detector.detect("")) == []
    assert asyncio.run(detector.detect("   ")) == []
